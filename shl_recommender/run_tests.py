"""Comprehensive test runner for SHL Recommender."""

import asyncio
import json
import sys
from typing import List, Dict, Any
import httpx
from pathlib import Path
from evaluation import TestTraceAnalyzer, EvaluationMetrics, BehaviorProbes


class ConversationSimulator:
    """Simulate conversations with the agent."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 30.0
    
    async def test_endpoint(self, endpoint: str, data: Dict = None) -> Dict:
        """Test an API endpoint."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if endpoint == "/health":
                response = await client.get(f"{self.base_url}{endpoint}")
            else:
                response = await client.post(f"{self.base_url}{endpoint}", json=data)
            
            return {
                "status_code": response.status_code,
                "data": response.json() if response.status_code == 200 else None,
                "error": response.text if response.status_code != 200 else None
            }
    
    async def run_conversation(self, turns: List[str]) -> List[Dict]:
        """Run a multi-turn conversation."""
        messages = []
        results = []
        
        for turn_idx, user_message in enumerate(turns):
            # Add user message
            messages.append({"role": "user", "content": user_message})
            
            # Get agent response
            response = await self.test_endpoint("/chat", {"messages": messages})
            
            if response["status_code"] == 200:
                agent_data = response["data"]
                messages.append({
                    "role": "assistant",
                    "content": agent_data["reply"]
                })
                
                results.append({
                    "turn": turn_idx + 1,
                    "user_message": user_message,
                    "agent_reply": agent_data["reply"],
                    "recommendations": agent_data.get("recommendations", []),
                    "end_of_conversation": agent_data.get("end_of_conversation", False)
                })
            else:
                results.append({
                    "turn": turn_idx + 1,
                    "error": response["error"],
                    "status_code": response["status_code"]
                })
                break
        
        return results


class TestRunner:
    """Run comprehensive tests."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.simulator = ConversationSimulator(base_url)
        self.results = {
            "health_check": None,
            "conversation_tests": [],
            "behavior_probes": [],
            "performance": {}
        }
    
    async def run_all_tests(self) -> Dict:
        """Run all tests."""
        print("=" * 60)
        print("SHL RECOMMENDER - COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        
        # Test 1: Health check
        await self._test_health()
        
        # Test 2: Sample conversations
        await self._test_conversations()
        
        # Test 3: Behavior probes
        await self._test_behavior_probes()
        
        # Test 4: Load test traces if available
        await self._test_with_traces()
        
        return self.results
    
    async def _test_health(self):
        """Test health endpoint."""
        print("\n[1/4] Testing Health Endpoint...")
        result = await self.simulator.test_endpoint("/health")
        
        if result["status_code"] == 200 and result["data"].get("status") == "ok":
            print("✓ Health check passed")
            self.results["health_check"] = "PASS"
        else:
            print("✗ Health check failed")
            self.results["health_check"] = "FAIL"
            return False
        
        return True
    
    async def _test_conversations(self):
        """Test sample conversations."""
        print("\n[2/4] Testing Sample Conversations...")
        
        test_conversations = [
            {
                "name": "Vague Initial Query",
                "turns": ["I need an assessment"],
                "expect_no_recommendations": True,
                "expect_clarification": True
            },
            {
                "name": "Specific Java Developer Role",
                "turns": [
                    "I'm hiring a Java developer with 4-5 years experience",
                    "Yes, they need to work with stakeholders too"
                ],
                "expect_recommendations": True
            },
            {
                "name": "Multi-turn with Refinement",
                "turns": [
                    "We need personality assessments for sales hires",
                    "Actually, let's focus on verbal communication skills too"
                ],
                "expect_recommendations": True
            }
        ]
        
        for conv in test_conversations:
            print(f"  Testing: {conv['name']}...")
            try:
                results = await self.simulator.run_conversation(conv["turns"])
                
                # Validate results
                success = True
                if conv.get("expect_no_recommendations"):
                    if results[-1].get("recommendations"):
                        success = False
                        print(f"    ✗ Unexpected recommendations on vague query")
                
                if conv.get("expect_recommendations"):
                    if not results[-1].get("recommendations"):
                        success = False
                        print(f"    ✗ No recommendations when expected")
                
                if success:
                    print(f"    ✓ {conv['name']} passed")
                
                self.results["conversation_tests"].append({
                    "name": conv["name"],
                    "status": "PASS" if success else "FAIL",
                    "turns": len(results),
                    "final_recommendations": len(results[-1].get("recommendations", []))
                })
            
            except Exception as e:
                print(f"    ✗ Error: {e}")
                self.results["conversation_tests"].append({
                    "name": conv["name"],
                    "status": "ERROR",
                    "error": str(e)
                })
    
    async def _test_behavior_probes(self):
        """Test behavior probes."""
        print("\n[3/4] Testing Behavior Probes...")
        
        probes = [
            {
                "name": "Refuses Off-Topic",
                "turns": ["What are good interview questions?"],
                "expect_refusal": True
            },
            {
                "name": "No Recs on Vague Turn 1",
                "turns": ["I need an assessment"],
                "expect_no_recommendations": True
            },
            {
                "name": "Turn Limit Respected",
                "turns": [
                    "Role 1", "Response 1",
                    "Role 2", "Response 2",
                    "Role 3", "Response 3",
                    "Role 4", "Response 4",
                    "Role 5"  # This would be turn 9, should be rejected
                ],
                "expect_turn_limit": True
            }
        ]
        
        for probe in probes:
            print(f"  Testing: {probe['name']}...")
            try:
                results = await self.simulator.run_conversation(probe["turns"])
                
                passed = False
                if probe.get("expect_refusal"):
                    # Check if agent refuses
                    last_reply = results[-1].get("agent_reply", "").lower()
                    passed = any(word in last_reply for word in ["cannot", "refuse", "off-topic", "not discuss"])
                
                elif probe.get("expect_no_recommendations"):
                    passed = len(results[-1].get("recommendations", [])) == 0
                
                elif probe.get("expect_turn_limit"):
                    passed = len(results) <= 8
                
                status = "PASS" if passed else "FAIL"
                print(f"    {('✓' if passed else '✗')} {probe['name']}")
                
                self.results["behavior_probes"].append({
                    "name": probe["name"],
                    "status": status
                })
            
            except Exception as e:
                print(f"    ✗ Error: {e}")
                self.results["behavior_probes"].append({
                    "name": probe["name"],
                    "status": "ERROR",
                    "error": str(e)
                })
    
    async def _test_with_traces(self):
        """Test with public test traces if available."""
        print("\n[4/4] Testing with Public Traces...")
        
        trace_analyzer = TestTraceAnalyzer()
        traces = trace_analyzer.load_traces()
        
        if not traces:
            print("  No test traces found in test_traces/ directory")
            return
        
        print(f"  Found {len(traces)} test traces")
        summary = trace_analyzer.get_summary()
        print(f"  Summary: {summary}")
    
    async def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        print(f"\nHealth Check: {self.results['health_check']}")
        
        if self.results["conversation_tests"]:
            print(f"\nConversation Tests: {len(self.results['conversation_tests'])}")
            for test in self.results["conversation_tests"]:
                status_symbol = "✓" if test["status"] == "PASS" else "✗"
                print(f"  {status_symbol} {test['name']}: {test['status']}")
        
        if self.results["behavior_probes"]:
            print(f"\nBehavior Probes: {len(self.results['behavior_probes'])}")
            for probe in self.results["behavior_probes"]:
                status_symbol = "✓" if probe["status"] == "PASS" else "✗"
                print(f"  {status_symbol} {probe['name']}: {probe['status']}")
        
        print("\n" + "=" * 60)


async def main():
    """Main test runner."""
    test_runner = TestRunner()
    
    try:
        await test_runner.run_all_tests()
        await test_runner.print_summary()
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
