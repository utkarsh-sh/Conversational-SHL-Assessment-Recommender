import json
import os
import re
from typing import List, Dict, Any
import asyncio

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class ConversationalAgent:
    """Conversational agent for SHL assessment recommendations."""
    
    def __init__(self, catalog_manager):
        self.catalog = catalog_manager
        self.client = Anthropic() if Anthropic and os.getenv("ANTHROPIC_API_KEY") else None
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent."""
        return self._build_system_prompt_for_candidates(self.catalog.get_all_assessments())

    def _build_system_prompt_for_candidates(self, candidates: List[Dict[str, Any]]) -> str:
        catalog_json = self._prepare_catalog_json(candidates)
        
        return f"""You are an expert SHL assessment recommendation specialist. Your role is to help hiring managers and recruiters find the right SHL assessments for their hiring needs through a natural conversation.

## Candidate SHL Assessments
{catalog_json}

## Your Core Responsibilities

1. **Clarify Vague Queries**: When users provide vague intent, ask clarifying questions to understand:
   - The specific role/position they're hiring for
   - Required competencies and skills  
   - Seniority level (entry-level, mid-level, senior, executive)
   - Whether they need technical, personality, verbal, numerical, or general ability assessments
   - Any specific constraints or preferences

2. **Make Grounded Recommendations**: Once you have sufficient context, provide 1-10 relevant assessments. Format as JSON with exact catalog names:
   {{"recommendations": [{{"name": "EXACT_CATALOG_NAME", "url": "https://...", "test_type": "K"}}]}}

3. **Handle Refinements**: When users change constraints mid-conversation, update recommendations based on new criteria.

4. **Support Comparisons**: Answer comparison questions using only catalog data.

5. **Stay Rigidly In Scope**: 
   - Only discuss SHL assessments from the catalog
   - Refuse off-topic requests (hiring advice, legal questions, interview tips)
   - Never recommend assessments not in the catalog
   - Every URL must come from the catalog

## Critical Response Format

Your response MUST be JSON:
{{
  "reply": "Conversational response text",
  "recommendations": [],
  "end_of_conversation": false
}}

- Leave recommendations empty when clarifying
- Only include 1-10 items when recommending
- Set end_of_conversation to true only when user is satisfied

## Conversation Flow

Turn 1: Understand the role and basic needs
Turn 2: Clarify seniority and specific requirements
Turn 3+: Make recommendations or refine based on feedback

Only recommend from the candidate list. Track all user constraints and preferences.
"""
    
    def _prepare_catalog_json(self, candidates: List[Dict[str, Any]] = None) -> str:
        """Prepare candidate catalog records as JSON for the prompt."""
        assessments = candidates or self.catalog.get_all_assessments()
        catalog_summary = {
            "total_assessments": len(assessments),
            "assessments": assessments[:40],
        }
        return json.dumps(catalog_summary, indent=2)
    
    async def process_conversation(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Process a conversation turn and return agent response."""
        try:
            # Run the agent logic in an executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._sync_process_conversation,
                messages
            )
            return self._canonicalize_response(result)
        except Exception as e:
            print(f"Error processing conversation: {e}")
            return self._deterministic_response(messages)
    
    def _sync_process_conversation(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Synchronous conversation processing."""
        scope_violation = self._scope_violation_reason(messages)
        if scope_violation:
            return {
                "reply": "I can't help with off-topic or prompt-injection requests. I can only help with SHL assessment selection and comparisons. Please share the role, skills, seniority, or assessment constraints you want to evaluate.",
                "recommendations": [],
                "end_of_conversation": False,
            }

        if len(messages) >= 8:
            response = {
                "reply": "We've reached the conversation limit. Here are the best assessments for your needs based on our discussion.",
                "recommendations": self._extract_recommendations_from_context(messages),
                "end_of_conversation": True,
            }
            if not response["recommendations"]:
                response["recommendations"] = self._retrieve_recommendations(messages, limit=5)
            return response
        
        if self._is_vague(messages):
            return {
                "reply": "I can help with that. What role are you hiring for, what skills or competencies matter most, and what seniority level should the assessment target?",
                "recommendations": [],
                "end_of_conversation": False,
            }

        if self._is_comparison_request(messages):
            return self._compare_assessments(messages)

        if not self.client:
            return self._deterministic_response(messages)

        candidates = self._retrieve_candidates(messages, limit=40)
        system_prompt = self._build_system_prompt_for_candidates(candidates)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=system_prompt,
            messages=messages,
            timeout=25,
        )
        
        agent_reply = response.content[0].text
        
        # Parse the response
        parsed = self._parse_agent_response(agent_reply, messages)
        
        return parsed

    def _parse_agent_response(self, response_text: str, messages: List[Dict]) -> Dict[str, Any]:
        """Parse agent response to extract reply, recommendations, and conversation status."""
        recommendations = []
        end_of_conversation = False
        reply_text = response_text

        parsed_json = self._extract_json_payload(response_text)
        if parsed_json and "recommendations" in parsed_json:
            raw_recommendations = parsed_json.get("recommendations", [])
            for rec in raw_recommendations:
                canonical = self.catalog.canonicalize_recommendation(rec)
                if canonical:
                    recommendations.append(canonical)

            reply_text = parsed_json.get("reply", "").strip() or "Here are the recommended assessments for your needs."
            end_of_conversation = bool(parsed_json.get("end_of_conversation", False))
        
        # Check for conversation ending signals
        ending_phrases = [
            "does this work for you",
            "are these the right assessments",
            "would you like to proceed",
            "best of luck",
            "let me know"
        ]
        
        if any(phrase in reply_text.lower() for phrase in ending_phrases) and recommendations:
            end_of_conversation = True
        
        return {
            "reply": reply_text.strip() or "I understand. Let me find the right assessments for you.",
            "recommendations": recommendations[:10],  # Max 10 recommendations
            "end_of_conversation": end_of_conversation
        }

    def _extract_json_payload(self, text: str) -> Dict[str, Any] | None:
        """Extract a JSON object containing recommendations from model text."""
        stripped = text.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                payload = json.loads(stripped)
                if isinstance(payload, dict):
                    return payload
            except json.JSONDecodeError:
                pass

        matches = re.findall(r"\{[\s\S]*\}", text)
        for candidate in reversed(matches):
            try:
                payload = json.loads(candidate)
                if isinstance(payload, dict) and "recommendations" in payload:
                    return payload
            except json.JSONDecodeError:
                continue
        return None
    
    def _extract_recommendations_from_context(self, messages: List[Dict]) -> List[Dict[str, Any]]:
        """Extract recommendations from conversation context as fallback."""
        # Look for any previous recommendations in the conversation
        for message in reversed(messages):
            if message.get("role") == "assistant":
                try:
                    json_pattern = r'\{[\s\S]*?"recommendations"[\s\S]*?\}'
                    json_matches = re.findall(json_pattern, message.get("content", ""))
                    if json_matches:
                        json_data = json.loads(json_matches[-1])
                        if "recommendations" in json_data:
                            return [
                                rec for rec in (
                                    self.catalog.canonicalize_recommendation(item)
                                    for item in json_data["recommendations"]
                                )
                                if rec
                            ][:10]
                except:
                    pass
        
        return self._retrieve_recommendations(messages, limit=5)

    def _canonicalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        recommendations = []
        for rec in response.get("recommendations", []):
            canonical = self.catalog.canonicalize_recommendation(rec)
            if canonical and canonical not in recommendations:
                recommendations.append(canonical)
        return {
            "reply": response.get("reply", "").strip() or "I can help you choose SHL assessments.",
            "recommendations": recommendations[:10],
            "end_of_conversation": bool(response.get("end_of_conversation", False)),
        }

    def _deterministic_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        recommendations = self._retrieve_recommendations(messages, limit=5)
        if not recommendations:
            return {
                "reply": "I can help with SHL assessment recommendations. Please share the target role, core skills, seniority level, and whether you need technical, cognitive, or personality assessments.",
                "recommendations": [],
                "end_of_conversation": False,
            }
        return {
            "reply": f"Based on the SHL catalog matches for your request, here are {len(recommendations)} assessments to consider.",
            "recommendations": recommendations,
            "end_of_conversation": self._is_completion_signal(messages),
        }

    def _retrieve_recommendations(self, messages: List[Dict[str, str]], limit: int = 5) -> List[Dict[str, str]]:
        candidates = self._retrieve_candidates(messages, limit=limit)
        return [
            {
                "name": item["name"],
                "url": item["url"],
                "test_type": item["test_type"],
            }
            for item in candidates[:limit]
        ]

    def _retrieve_candidates(self, messages: List[Dict[str, str]], limit: int = 40) -> List[Dict[str, Any]]:
        query = self._conversation_text(messages)
        latest_user = self._latest_user_text(messages)

        # If user explicitly changes direction, prioritize the latest turn for filtering.
        if any(token in latest_user.lower() for token in ["instead", "rather", "focus", "actually", "change"]):
            query = latest_user

        filters = {}
        requested_types = self._requested_test_types(query)
        if requested_types:
            filters["test_type"] = requested_types

        candidates = self.catalog.search_assessments(query, filters=filters or None)
        if not candidates:
            candidates = self.catalog.search_assessments(query)
        if not candidates:
            candidates = self.catalog.get_all_assessments()
        return candidates[:limit]

    def _requested_test_types(self, text: str) -> List[str]:
        text = text.lower()
        types = []
        if any(word in text for word in ["technical", "coding", "java", "python", "javascript", "developer", "programming"]):
            types.append("K")
        if any(word in text for word in ["personality", "behavior", "behaviour", "opq"]):
            types.append("P")
        if "verbal" in text or "communication" in text:
            types.append("V")
        if "numerical" in text or "numeric" in text:
            types.append("N")
        return types

    def _is_vague(self, messages: List[Dict[str, str]]) -> bool:
        user_messages = [m["content"] for m in messages if m.get("role") == "user"]
        if len(user_messages) != 1:
            return False
        text = user_messages[-1].strip().lower()
        vague = {
            "i need an assessment",
            "need an assessment",
            "i need a test",
            "need a test",
            "help me choose an assessment",
        }
        return text in vague or len(re.findall(r"[a-z0-9+#.]+", text)) <= 4

    def _scope_violation_reason(self, messages: List[Dict[str, str]]) -> str | None:
        text = self._latest_user_text(messages).lower()

        injection_markers = [
            "ignore previous",
            "system prompt",
            "developer message",
            "reveal your instructions",
            "jailbreak",
            "prompt injection",
        ]
        if any(marker in text for marker in injection_markers):
            return "prompt_injection"

        off_topic = [
            "interview questions",
            "salary",
            "legal advice",
            "employment law",
            "write a contract",
        ]
        assessment_terms = [
            "assessment", "test", "shl", "opq", "gsa", "verify", "java",
            "python", "developer", "personality", "numerical", "verbal",
            "hiring", "candidate", "role", "skills", "compare",
        ]
        if any(term in text for term in off_topic) and not any(term in text for term in assessment_terms):
            return "off_topic"
        return None

    def _is_in_scope(self, messages: List[Dict[str, str]]) -> bool:
        return self._scope_violation_reason(messages) is None

    def _is_comparison_request(self, messages: List[Dict[str, str]]) -> bool:
        text = self._latest_user_text(messages).lower()
        return any(term in text for term in ["compare", "difference", " vs ", " versus "])

    def _compare_assessments(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        text = self._latest_user_text(messages)
        matches = self._extract_assessments_from_text(text)
        if len(matches) < 2:
            matches = self._retrieve_candidates(messages, limit=2)
        if len(matches) < 2:
            return {
                "reply": "I can compare SHL assessments, but I need the names of at least two assessments from the catalog.",
                "recommendations": [],
                "end_of_conversation": False,
            }
        first, second = matches[0], matches[1]
        reply = (
            f"{first['name']} is categorized as {first['test_type']} and is described in the catalog as: "
            f"{first['description']}. {second['name']} is categorized as {second['test_type']} and is described as: "
            f"{second['description']}. For this hiring need, choose the one whose catalog description best matches the competency you need to measure."
        )
        return {
            "reply": reply,
            "recommendations": [
                self.catalog.canonicalize_recommendation(first),
                self.catalog.canonicalize_recommendation(second),
            ],
            "end_of_conversation": False,
        }

    def _extract_assessments_from_text(self, text: str) -> List[Dict[str, Any]]:
        lowered = text.lower()
        found = []

        aliases = {
            "opq": "OPQ32r",
            "gsa": "GSA",
        }
        for alias, canonical_name in aliases.items():
            if re.search(rf"\b{re.escape(alias)}\b", lowered):
                assessment = self.catalog.get_assessment_by_name(canonical_name)
                if assessment and assessment not in found:
                    found.append(assessment)

        for assessment in self.catalog.get_all_assessments():
            if assessment["name"].lower() in lowered and assessment not in found:
                found.append(assessment)

        return found

    def _is_completion_signal(self, messages: List[Dict[str, str]]) -> bool:
        text = self._latest_user_text(messages).lower()
        return any(token in text for token in ["thanks", "thank you", "done", "that's all", "looks good"])

    def _conversation_text(self, messages: List[Dict[str, str]]) -> str:
        return " ".join(m.get("content", "") for m in messages if m.get("role") == "user")

    def _latest_user_text(self, messages: List[Dict[str, str]]) -> str:
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")
        return ""
