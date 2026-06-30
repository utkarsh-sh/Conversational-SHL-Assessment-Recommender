import json
import re
from typing import List, Dict, Optional, Any
from anthropic import Anthropic
import asyncio


class ConversationalAgent:
    """Conversational agent for SHL assessment recommendations."""
    
    def __init__(self, catalog_manager):
        self.catalog = catalog_manager
        self.client = Anthropic()
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the agent."""
        catalog_json = self._prepare_catalog_json()
        
        return f"""You are an expert SHL assessment recommendation specialist. Your role is to help hiring managers and recruiters find the right SHL assessments for their hiring needs through a natural conversation.

## Available SHL Assessments Catalog
{catalog_json}

## Your Core Responsibilities

1. **Clarify Vague Queries**: When users provide vague intent, ask clarifying questions to understand:
   - The specific role/position they're hiring for
   - Required competencies and skills  
   - Seniority level (entry-level, mid-level, senior, executive)
   - Whether they need technical, personality, verbal, numerical, or general ability assessments
   - Any specific constraints or preferences

2. **Make Grounded Recommendations**: Once you have sufficient context (usually after 2-3 clarifying turns), provide 1-10 relevant assessments. Format as JSON with exact catalog names:
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
Turn 3: Confirm assessment types (technical vs behavioral)
Turn 4+: Make recommendations or refine based on feedback

Aim to recommend by turn 4. Track all user constraints and preferences.
"""
    
    def _prepare_catalog_json(self) -> str:
        """Prepare the catalog as JSON for the prompt."""
        assessments = self.catalog.get_all_assessments()
        catalog_summary = {
            "total_assessments": len(assessments),
            "assessments": assessments[:20]  # Include first 20 for prompt, avoid token limits
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
            return result
        except Exception as e:
            print(f"Error processing conversation: {e}")
            return {
                "reply": "I encountered an error processing your request. Please try again.",
                "recommendations": [],
                "end_of_conversation": False
            }
    
    def _sync_process_conversation(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Synchronous conversation processing."""
        # Check conversation length limit
        if len(messages) >= 8:
            return {
                "reply": "We've reached the conversation limit. Here are the best assessments for your needs based on our discussion.",
                "recommendations": self._extract_recommendations_from_context(messages),
                "end_of_conversation": True
            }
        
        # Add system prompt
        system_messages = [{"role": "user", "content": self.system_prompt}]
        
        # Create API call with conversation history
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            system=self.system_prompt,
            messages=messages
        )
        
        agent_reply = response.content[0].text
        
        # Parse the response
        parsed = self._parse_agent_response(agent_reply, messages)
        
        return parsed
    
    def _parse_agent_response(self, response_text: str, messages: List[Dict]) -> Dict[str, Any]:
        """Parse agent response to extract reply, recommendations, and conversation status."""
        recommendations = []
        end_of_conversation = False
        
        # Check for JSON-formatted recommendations in the response
        json_pattern = r'\{[\s\S]*?"recommendations"[\s\S]*?\}'
        json_matches = re.findall(json_pattern, response_text)
        
        reply_text = response_text
        
        if json_matches:
            try:
                # Extract the last JSON match (most likely the recommendations)
                json_str = json_matches[-1]
                json_data = json.loads(json_str)
                
                if "recommendations" in json_data:
                    raw_recommendations = json_data["recommendations"]
                    
                    # Validate and clean recommendations
                    for rec in raw_recommendations:
                        if self.catalog.validate_assessment(rec.get("name", "")):
                            recommendations.append({
                                "name": rec["name"],
                                "url": rec.get("url", ""),
                                "test_type": rec.get("test_type", "G")
                            })
                    
                    # Remove JSON from reply text
                    reply_text = response_text[:json_matches[-1].find(json_str)].strip()
                    if not reply_text:
                        reply_text = "Here are the recommended assessments for your needs."
                    
                    # If we have recommendations, conversation may be ending
                    if recommendations and len(messages) >= 4:
                        end_of_conversation = True
            
            except json.JSONDecodeError:
                pass  # If JSON parsing fails, just use the full response
        
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
                            return json_data["recommendations"][:10]
                except:
                    pass
        
        # Return general recommendations as fallback
        return [
            {
                "name": "OPQ32r",
                "url": "https://www.shl.com/solutions/products/opq32r/",
                "test_type": "P"
            }
        ]
