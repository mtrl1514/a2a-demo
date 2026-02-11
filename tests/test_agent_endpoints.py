#!/usr/bin/env python3
"""
Test script to verify that the research and analysis agents' HTTP endpoints work correctly.
This helps verify the direct orchestrator can communicate with them.
"""

import asyncio
import httpx
import json
import sys


async def test_research_agent():
    """Test the research agent HTTP endpoint."""
    print("[TEST] Testing Research Agent at http://localhost:9101")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:9101/invoke",
                json={
                    "message": {
                        "parts": [{"root": {"text": "Test query: Tell me about artificial intelligence"}}]
                    }
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.text
                print(f"✅ Research Agent Response: {result[:200]}...")
                return True
            else:
                print(f"❌ Research Agent Error: Status {response.status_code}")
                print(f"   Response: {response.text}")
                return False

    except Exception as e:
        print(f"❌ Research Agent Connection Error: {e}")
        return False


async def test_analysis_agent():
    """Test the analysis agent HTTP endpoint."""
    print("[TEST] Testing Analysis Agent at http://localhost:9102")

    # Mock research data for testing
    test_research_data = json.dumps({
        "topic": "Artificial Intelligence",
        "summary": "AI is a broad field of computer science focused on creating intelligent machines.",
        "findings": [
            {"title": "Machine Learning", "description": "A subset of AI that enables computers to learn without being explicitly programmed."},
            {"title": "Neural Networks", "description": "Computing systems inspired by biological neural networks."}
        ],
        "sources": "Based on general knowledge"
    })

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:9102/invoke",
                json={
                    "message": {
                        "parts": [{"root": {"text": test_research_data}}]
                    }
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.text
                print(f"✅ Analysis Agent Response: {result[:200]}...")
                return True
            else:
                print(f"❌ Analysis Agent Error: Status {response.status_code}")
                print(f"   Response: {response.text}")
                return False

    except Exception as e:
        print(f"❌ Analysis Agent Connection Error: {e}")
        return False


async def main():
    """Run all agent endpoint tests."""
    print("=" * 80)
    print("[INFO] Testing A2A Agent HTTP Endpoints")
    print("=" * 80)
    print("[INFO] Make sure both agents are running:")
    print("   - Research Agent: npm run dev:research")
    print("   - Analysis Agent: npm run dev:analysis")
    print("=" * 80)

    research_ok = await test_research_agent()
    print()
    analysis_ok = await test_analysis_agent()

    print("\n" + "=" * 80)
    if research_ok and analysis_ok:
        print("✅ ALL TESTS PASSED - Both agents are responding correctly")
        print("✅ Direct orchestrator should be able to communicate with them")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - Check agent status and try again")
        print("❌ Direct orchestrator may not work until agents are fixed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())