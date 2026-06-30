#!/usr/bin/env python3
"""Local testing script for the SHL Recommender API."""

import asyncio
import json
import httpx
from typing import List, Dict


async def test_health():
    """Test the health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200


async def test_chat(messages: List[Dict[str, str]]):
    """Test the chat endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {"messages": messages}
        response = await client.post(
            "http://localhost:8000/chat",
            json=payload
        )
        print(f"Chat response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"Error: {response.text}")
        return None


async def run_conversation_test():
    """Run a sample conversation test."""
    print("\n=== Testing Single-Turn Chat ===")
    
    messages = [
        {
            "role": "user",
            "content": "I'm hiring a Java developer who needs to work with stakeholders"
        }
    ]
    
    result = await test_chat(messages)
    
    if result:
        # Continue the conversation
        print("\n=== Testing Multi-Turn Chat ===")
        messages.append({
            "role": "assistant",
            "content": result["reply"]
        })
        messages.append({
            "role": "user",
            "content": "Mid-level, around 4 years of experience"
        })
        
        result2 = await test_chat(messages)
        if result2 and result2.get("recommendations"):
            print(f"\nGot {len(result2['recommendations'])} recommendations")


async def main():
    """Run all tests."""
    print("Testing SHL Recommender API...\n")
    
    # Test health first
    health_ok = await test_health()
    if not health_ok:
        print("Health check failed. Is the server running?")
        return
    
    # Test conversations
    await run_conversation_test()
    
    print("\n=== Tests Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
