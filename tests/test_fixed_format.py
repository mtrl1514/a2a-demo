#!/usr/bin/env python3
"""
Test the corrected A2A message format
"""

import requests
import json

def test_research_agent():
    """Test Research Agent with correct A2A format"""

    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": 1,
        "params": {
            "message": {
                "messageId": "test-msg-1",
                "role": "user",
                "parts": [{"text": "research artificial intelligence"}]
            }
        }
    }

    try:
        response = requests.post(
            "http://localhost:9101/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print("SUCCESS: Research Agent responded!")
                print(f"Response: {result['result'][:200]}...")
                return True
            else:
                print(f"ERROR: Unexpected response format: {result}")
                return False
        else:
            print(f"ERROR: HTTP {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_analysis_agent():
    """Test Analysis Agent with correct A2A format"""

    test_data = '{"topic": "AI", "summary": "Test data", "findings": [{"title": "Test", "description": "Test"}]}'

    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": 2,
        "params": {
            "message": {
                "messageId": "test-msg-2",
                "role": "user",
                "parts": [{"text": test_data}]
            }
        }
    }

    try:
        response = requests.post(
            "http://localhost:9102/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print("SUCCESS: Analysis Agent responded!")
                print(f"Response: {result['result'][:200]}...")
                return True
            else:
                print(f"ERROR: Unexpected response format: {result}")
                return False
        else:
            print(f"ERROR: HTTP {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("Testing corrected A2A message format...")
    print("=" * 50)

    success_count = 0

    print("Testing Research Agent...")
    if test_research_agent():
        success_count += 1

    print("\nTesting Analysis Agent...")
    if test_analysis_agent():
        success_count += 1

    print("=" * 50)
    print(f"Results: {success_count}/2 agents working")

    if success_count == 2:
        print("ALL TESTS PASSED! The Direct Orchestrator should now work correctly.")
    else:
        print("Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()