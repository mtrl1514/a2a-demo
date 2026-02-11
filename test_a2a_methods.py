#!/usr/bin/env python3
"""
Test script to find the correct JSON-RPC method name for A2A agents.
"""

import requests
import json

def test_method(method_name, agent_url="http://localhost:9101"):
    """Test a specific JSON-RPC method name"""
    payload = {
        "jsonrpc": "2.0",
        "method": method_name,
        "id": 1,
        "params": {
            "message": {
                "parts": [{"root": {"text": "test query"}}]
            }
        }
    }

    try:
        response = requests.post(
            f"{agent_url}/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        result = response.json()

        if response.status_code == 200 and "result" in result:
            print(f"✅ SUCCESS: Method '{method_name}' works!")
            print(f"   Response: {result['result'][:100]}...")
            return True
        elif "error" in result and result["error"]["code"] == -32601:
            print(f"❌ Method '{method_name}' not found")
            return False
        else:
            print(f"⚠️  Method '{method_name}' returned: {result}")
            return False

    except Exception as e:
        print(f"💥 Error testing '{method_name}': {e}")
        return False

def main():
    print("Testing A2A Agent JSON-RPC methods...")
    print("=" * 50)

    # Common method names to try
    methods_to_test = [
        "invoke",
        "execute",
        "run",
        "call",
        "process",
        "handle",
        "task",
        "agent",
        "research",
        "query",
        "ask",
        "submit",
        "send"
    ]

    working_methods = []

    for method in methods_to_test:
        if test_method(method):
            working_methods.append(method)

    print("=" * 50)
    if working_methods:
        print(f"🎉 Found working methods: {working_methods}")
    else:
        print("😞 No working methods found")

if __name__ == "__main__":
    main()