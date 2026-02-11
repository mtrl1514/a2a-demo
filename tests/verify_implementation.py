#!/usr/bin/env python3
"""
Verification script to test both orchestrator approaches and compare results.
This helps identify whether the issue is with A2A middleware or elsewhere.
"""

import asyncio
import httpx
import json
import os
from typing import Optional


class OrchestratorTester:
    """Test both orchestrator implementations."""

    def __init__(self):
        self.standard_url = "http://localhost:9100"
        self.direct_url = "http://localhost:9103"
        self.test_query = "Research machine learning basics"

    async def test_orchestrator(self, url: str, name: str) -> dict:
        """Test a single orchestrator endpoint."""
        print(f"[TEST] Testing {name} at {url}")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # AG-UI protocol expects this format
                response = await client.post(
                    f"{url}/",
                    json={
                        "messages": [
                            {
                                "role": "user",
                                "content": self.test_query
                            }
                        ]
                    },
                    headers={"Content-Type": "application/json"}
                )

                result = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_preview": response.text[:300] + "..." if len(response.text) > 300 else response.text,
                    "error": None
                }

                if response.status_code == 200:
                    print(f"✅ {name}: SUCCESS")
                    print(f"   Response preview: {result['response_preview']}")
                else:
                    print(f"❌ {name}: HTTP {response.status_code}")
                    print(f"   Error: {response.text}")

                return result

        except Exception as e:
            result = {
                "success": False,
                "status_code": None,
                "response_preview": None,
                "error": str(e)
            }
            print(f"❌ {name}: Connection failed - {e}")
            return result

    async def check_agent_availability(self) -> dict:
        """Check if required agents are running."""
        agents = {
            "research": "http://localhost:9101",
            "analysis": "http://localhost:9102"
        }

        status = {}

        for name, url in agents.items():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{url}/")
                    status[name] = response.status_code in [200, 404]  # 404 is ok, means server is running
            except:
                status[name] = False

        return status

    async def run_comparison_test(self):
        """Run comprehensive comparison between both approaches."""
        print("=" * 80)
        print("ORCHESTRATOR COMPARISON TEST")
        print("=" * 80)

        # Check prerequisites
        print("[PREREQ] Checking agent availability...")
        agent_status = await self.check_agent_availability()

        all_agents_ready = all(agent_status.values())

        for agent, ready in agent_status.items():
            status = "✅ Ready" if ready else "❌ Not responding"
            print(f"   {agent.capitalize()} Agent: {status}")

        if not all_agents_ready:
            print("\n❌ PREREQUISITE FAILED: Not all agents are running")
            print("   Start agents with: npm run dev:research && npm run dev:analysis")
            return

        print(f"\n[QUERY] Testing with: '{self.test_query}'")
        print("=" * 80)

        # Test both orchestrators
        direct_result = await self.test_orchestrator(self.direct_url, "Direct Orchestrator")
        print()
        standard_result = await self.test_orchestrator(self.standard_url, "A2A Middleware Orchestrator")

        # Analysis
        print("\n" + "=" * 80)
        print("RESULTS ANALYSIS")
        print("=" * 80)

        if direct_result["success"] and standard_result["success"]:
            print("✅ BOTH APPROACHES WORKING")
            print("   → Issue may be intermittent or environment-specific")
            print("   → Try testing through the frontend UI")

        elif direct_result["success"] and not standard_result["success"]:
            print("✅ ISSUE ISOLATED TO A2A MIDDLEWARE")
            print("   → Direct orchestrator works correctly")
            print("   → A2A middleware has integration problems")
            print("   → Use direct orchestrator as workaround")

        elif not direct_result["success"] and standard_result["success"]:
            print("❌ UNEXPECTED: A2A middleware working, direct failing")
            print("   → Check direct orchestrator configuration")
            print("   → Verify HTTP tool implementation")

        else:
            print("❌ BOTH APPROACHES FAILING")
            print("   → Issue is deeper than A2A middleware")
            print("   → Check AG-UI protocol or Bedrock configuration")
            print("   → Verify AWS credentials and model access")

        # Recommendations
        print("\n[RECOMMENDATIONS]")
        if direct_result["success"]:
            print("• Set USE_DIRECT_ORCHESTRATOR=true in .env for development")
            print("• Use npm run dev-direct for testing")

        if not standard_result["success"]:
            print("• Check A2A middleware logs for tool call ID errors")
            print("• Consider reporting the issue to A2A middleware maintainers")

        print("\n[NEXT STEPS]")
        print("• Test through frontend UI at http://localhost:3000")
        print("• Monitor logs for detailed error information")
        print("• Compare message histories between approaches")


async def main():
    """Main test runner."""
    tester = OrchestratorTester()
    await tester.run_comparison_test()


if __name__ == "__main__":
    asyncio.run(main())