"""
Direct Orchestrator Agent - Bypasses A2A middleware for testing.
Makes direct HTTP calls to Research and Analysis agents.
Uses Pydantic AI with AWS Bedrock.
"""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
import sys
import json
import logging
import uvicorn
import httpx
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.bedrock import BedrockConverseModel, BedrockModelSettings
from pydantic_ai.providers.bedrock import BedrockProvider

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================
# 환경 변수 로드 및 검증
# ========================================

# Bedrock 설정 (환경 변수에서 로드)
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', None)
BEDROCK_REGION = os.getenv('BEDROCK_REGION', 'ap-northeast-2')

if not BEDROCK_MODEL_ID:
    logger.critical('❌ Need to specify BEDROCK_MODEL_ID in environment')
    logger.critical('   Example: BEDROCK_MODEL_ID=apac.anthropic.claude-sonnet-4-20250514-v1:0')
    sys.exit(1)

# Server 설정 (포트 9103으로 변경)
ORCHESTRATOR_DIRECT_PORT = int(os.getenv("ORCHESTRATOR_DIRECT_PORT", 9103))

# Agent URLs
RESEARCH_AGENT_URL = os.getenv('RESEARCH_AGENT_URL', 'http://localhost:9101')
ANALYSIS_AGENT_URL = os.getenv('ANALYSIS_AGENT_URL', 'http://localhost:9102')

# ========================================
# Agent Creation (must be done first)
# ========================================

logger.info(f"[INIT] Initializing AWS Bedrock provider")
logger.info(f"   Model: {BEDROCK_MODEL_ID}")
logger.info(f"   Region: {BEDROCK_REGION}")
logger.info(f"   Credentials: Using ~/.aws/credentials")

# Bedrock 모델 설정
bedrock_settings = BedrockModelSettings(
    parallel_tool_calls=False,  # Sequential execution needed
    # Prompt caching 활성화 (비용 절감)
    bedrock_cache_messages=True,
    bedrock_cache_instructions=True,
    bedrock_cache_tool_definitions=True,
)

# Bedrock Provider 생성 (AWS credentials는 자동으로 ~/.aws/credentials에서 로드)
bedrock_provider = BedrockProvider(
    region_name=BEDROCK_REGION,
)

# Bedrock 모델 생성
bedrock_model = BedrockConverseModel(
    model_name=BEDROCK_MODEL_ID,
    provider=bedrock_provider
)

logger.info(f"✅ AWS Bedrock provider initialized successfully")

# System Prompt - Direct HTTP tools 사용을 위해 수정
system_prompt = """
You are a research orchestrator. Your goal is to provide a complete research and analysis report by collaborating with specialized agents through direct HTTP calls.

**TOOLS AVAILABLE:**
- `call_research_agent(query, instruction)`: Make direct HTTP call to Research Agent. Use 'instruction' parameter to provide detailed research instructions.
- `call_analysis_agent(research_data, instruction)`: Make direct HTTP call to Analysis Agent. Use 'instruction' parameter to specify what analysis to perform.

**WORKFLOW:**
You MUST execute the following steps sequentially in a single turn:
1. **Research**: Call `call_research_agent` with both the user's query AND a detailed instruction describing exactly what you want the research agent to investigate.
2. **Analysis**: Once you receive the research findings, immediately call `call_analysis_agent` with the complete research data AND a detailed instruction describing what specific analysis you want performed.
3. **Final Report**: Synthesize both results into a structured, professional report for the user.

**CRITICAL**: Always provide detailed instructions in the 'instruction' parameter for both tools. These instructions will be shown to users in the frontend, so make them comprehensive and clear about what you're asking each agent to do.

Examples:
- Research instruction: "Research Pydantic AI comprehensively, including its core features, architectural design, key benefits, use cases, recent developments, and ecosystem comparisons"
- Analysis instruction: "Analyze the research findings to identify key market trends, competitive advantages, technical strengths/weaknesses, and provide strategic recommendations for adoption"

**IMPORTANT FOR FRONTEND DISPLAY**: You MUST call both tools explicitly so the user can see the A2A message flow visualization. Do not skip the `call_analysis_agent` tool call.

**CRITICAL DATA FORMATTING REQUIREMENT**:
Your final response is REQUIRED to include two parts:

1. A professional summary for the user explaining your findings
2. The exact JSON data from both agents using these MANDATORY markers:

RESEARCH_DATA_START: [paste the complete JSON object from research agent] :RESEARCH_DATA_END
ANALYSIS_DATA_START: [paste the complete JSON object from analysis agent] :ANALYSIS_DATA_END

**EXAMPLE RESPONSE FORMAT:**
```
Based on my research and analysis of [topic], I found [summary of key insights]...

RESEARCH_DATA_START: {"topic": "Quantum Computing", "summary": "Quantum computing represents...", "findings": [{"title": "Key Point 1", "description": "Details..."}], "sources": "Based on current research..."} :RESEARCH_DATA_END

ANALYSIS_DATA_START: {"topic": "Quantum Computing", "overview": "The analysis reveals...", "insights": [{"title": "Critical Insight", "description": "Analysis...", "importance": "High impact"}], "conclusion": "Overall conclusion..."} :ANALYSIS_DATA_END
```

**FAILURE TO INCLUDE THESE MARKERS WILL BREAK THE UI** - The frontend absolutely requires these markers to display the structured data properly.

**CRITICAL RULES:**
- Do NOT wait for user permission between steps.
- Use tools ONE AT A TIME (sequentially).
- You must complete both Research and Analysis phases before giving your final answer.
- Pass the complete research results to the analysis agent.
"""

# Agent 생성 - Direct HTTP tools 포함
orchestrator_agent = Agent(
    model=bedrock_model,
    system_prompt=system_prompt,
    model_settings=bedrock_settings,
    name='orchestrator_direct_agent',
    retries=2,
)

logger.info(f"✅ Agent '{orchestrator_agent.name}' created successfully")

# ========================================
# Custom Tools for Direct HTTP Communication (using decorators)
# ========================================

@orchestrator_agent.tool
async def call_research_agent(ctx: RunContext, query: str, instruction: str) -> str:
    """Call research agent directly via HTTP to gather information about a topic.

    Args:
        query: The basic research query
        instruction: Detailed instruction for what the agent should research (REQUIRED for frontend display)
    """
    # Debug logging to track parameter passing
    logger.info(f"[DEBUG] Tool called with query='{query}', instruction='{instruction}'")

    # Use the instruction as the primary research task
    research_task = instruction
    logger.info(f"[HTTP] Calling Research Agent: {research_task}")

    # Store the instruction in context for frontend access
    if hasattr(ctx, 'deps') and ctx.deps:
        ctx.deps['research_instruction'] = research_task

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # A2A agents expect JSON-RPC format at root endpoint
            response = await client.post(
                f"{RESEARCH_AGENT_URL}/",
                json={
                    "jsonrpc": "2.0",
                    "method": "message/send",
                    "id": 1,
                    "params": {
                        "message": {
                            "messageId": f"msg-{1}",
                            "role": "user",
                            "parts": [{"text": research_task}]  # Send the detailed instruction
                        }
                    }
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            response_json = response.json()
            # Extract result from JSON-RPC response
            if "result" in response_json:
                result = response_json["result"]
                logger.info(f"[HTTP] Research Agent Response: {str(result)[:200]}...")

                # Extract JSON from the message structure
                if isinstance(result, dict) and "parts" in result:
                    for part in result["parts"]:
                        if "text" in part:
                            return part["text"]

                return str(result)
            else:
                error = response_json.get("error", "Unknown error")
                logger.error(f"[HTTP] Research Agent Error: {error}")
                return f"Error: {error}"

    except Exception as e:
        error_msg = f"❌ Failed to call Research Agent: {str(e)}"
        logger.error(error_msg)
        return error_msg

@orchestrator_agent.tool
async def call_analysis_agent(ctx: RunContext, research_data: str, instruction: str) -> str:
    """Call analysis agent directly via HTTP to analyze research findings.

    Args:
        research_data: The research data to analyze
        instruction: Detailed instruction for what analysis to perform (REQUIRED for frontend display)
    """
    # Debug logging to track parameter passing
    logger.info(f"[DEBUG] Analysis tool called with instruction='{instruction}'")

    # Create a comprehensive analysis request with the instruction
    analysis_request = f"INSTRUCTION: {instruction}\n\nRESEARCH DATA TO ANALYZE:\n{research_data}"

    logger.info(f"[HTTP] Calling Analysis Agent with research data and instruction")

    # Store the instruction in context for frontend access
    if hasattr(ctx, 'deps') and ctx.deps:
        ctx.deps['analysis_instruction'] = instruction

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # A2A agents expect JSON-RPC format at root endpoint
            response = await client.post(
                f"{ANALYSIS_AGENT_URL}/",
                json={
                    "jsonrpc": "2.0",
                    "method": "message/send",
                    "id": 2,
                    "params": {
                        "message": {
                            "messageId": f"msg-{2}",
                            "role": "user",
                            "parts": [{"text": analysis_request}]
                        }
                    }
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            response_json = response.json()
            # Extract result from JSON-RPC response
            if "result" in response_json:
                result = response_json["result"]
                logger.info(f"[HTTP] Analysis Agent Response: {str(result)[:200]}...")

                # Extract JSON from the message structure
                if isinstance(result, dict) and "parts" in result:
                    for part in result["parts"]:
                        if "text" in part:
                            return part["text"]

                return str(result)
            else:
                error = response_json.get("error", "Unknown error")
                logger.error(f"[HTTP] Analysis Agent Error: {error}")
                return f"Error: {error}"

    except Exception as e:
        error_msg = f"❌ Failed to call Analysis Agent: {str(e)}"
        logger.error(error_msg)
        return error_msg

logger.info(f"[READY] Agent has direct HTTP tools for research and analysis agents")

# ========================================
# AG-UI ASGI 앱 생성 (agent.to_ag_ui() 사용)
# ========================================

# AG-UI 프로토콜을 지원하는 ASGI 앱 생성
app = orchestrator_agent.to_ag_ui(
    infer_name=False,  # Agent 이름 자동 추론 비활성화
    model_settings=bedrock_settings, # parallel_tool_calls=False 포함
    debug=True
)

logger.info(f"✅ AG-UI ASGI app created successfully")

# ========================================
# 서버 실행
# ========================================

if __name__ == "__main__":
    print("=" * 80)
    print(f"[START] Starting Direct Orchestrator Agent")
    print("=" * 80)
    print(f"[INFO] Server URL: http://localhost:{ORCHESTRATOR_DIRECT_PORT}")
    print(f"[INFO] Provider: AWS Bedrock")
    print(f"[INFO] Model: {BEDROCK_MODEL_ID}")
    print(f"[INFO] Region: {BEDROCK_REGION}")
    print(f"[INFO] Credentials: Using ~/.aws/credentials")
    print(f"[INFO] Prompt Caching: ENABLED")
    print(f"[INFO] AG-UI Protocol: ENABLED (via agent.to_ag_ui())")
    print(f"[INFO] Communication: DIRECT HTTP CALLS")
    print(f"[INFO] Research Agent: {RESEARCH_AGENT_URL}")
    print(f"[INFO] Analysis Agent: {ANALYSIS_AGENT_URL}")
    print(f"[INFO] Parallel Tool Calls: DISABLED (Sequential execution)")
    print("=" * 80)
    print(f"[TIP] This agent bypasses A2A middleware for testing")
    print(f"[TIP] Access the agent at: POST http://localhost:{ORCHESTRATOR_DIRECT_PORT}/")
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=ORCHESTRATOR_DIRECT_PORT)