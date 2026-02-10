"""
Orchestrator Agent - Coordinates between Research and Analysis agents.
Speaks AG-UI Protocol to the UI, delegates tasks to A2A agents via middleware.
Uses Pydantic AI with AWS Bedrock.
"""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
import sys
import logging
import uvicorn
from pydantic_ai import Agent, RunContext  # RunContext 임포트 추가
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

# Server 설정
ORCHESTRATOR_PORT = int(os.getenv("ORCHESTRATOR_PORT", 9100))

# ========================================
# Agent 생성
# ========================================

logger.info(f"[INIT] Initializing AWS Bedrock provider")
logger.info(f"   Model: {BEDROCK_MODEL_ID}")
logger.info(f"   Region: {BEDROCK_REGION}")
logger.info(f"   Credentials: Using ~/.aws/credentials")

# Bedrock 모델 설정
bedrock_settings = BedrockModelSettings(
    parallel_tool_calls=False,  # A2A에서는 순차 실행 필요
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

# System Prompt - A2A middleware tool 사용을 위해 수정
system_prompt = """
You are a research orchestrator. Your goal is to provide a complete research and analysis report by collaborating with specialized agents.

**TOOLS AVAILABLE:**
- `send_message_to_a2a_agent`: Use this tool to communicate with other agents. It requires two arguments:
    1. `agent_name`: The name of the agent ('Research Agent' or 'Analysis Agent').
    2. `message`: The specific instruction or data for that agent.

**WORKFLOW:**
You MUST execute the following steps sequentially in a single turn:
1. **Research**: Call `send_message_to_a2a_agent` with 'Research Agent' to gather information about the topic.
2. **Analysis**: Once you receive the research findings, immediately call `send_message_to_a2a_agent` with 'Analysis Agent' to get deep insights.
3. **Final Report**: Synthesize both results into a structured, professional report for the user.

**CRITICAL RULES:**
- Do NOT wait for user permission between steps.
- Use tools ONE AT A TIME (sequentially).
- You must complete both Research and Analysis phases before giving your final answer.
"""

# Agent 생성 - A2A middleware tool을 받을 준비
orchestrator_agent = Agent(
    model=bedrock_model,
    system_prompt=system_prompt,  # system_prompt 파라미터 사용
    model_settings=bedrock_settings,
    name='orchestrator_agent',
    retries=2,
)

logger.info(f"✅ Agent '{orchestrator_agent.name}' created successfully")
logger.info(f"[READY] Agent is ready to receive send_message_to_a2a_agent tool from A2A middleware")


# ========================================
# AG-UI ASGI 앱 생성 (agent.to_ag_ui() 사용)
# ========================================

# AG-UI 프로토콜을 지원하는 ASGI 앱 생성
app = orchestrator_agent.to_ag_ui(
    infer_name=False,  # Agent 이름 자동 추론 비활성화
    model_settings=bedrock_settings, # 이미 정의한 parallel_tool_calls=False 포함
    debug=True
)

logger.info(f"✅ AG-UI ASGI app created successfully")

# ========================================
# 서버 실행
# ========================================

if __name__ == "__main__":
    print("=" * 80)
    print(f"[START] Starting Orchestrator Agent")
    print("=" * 80)
    print(f"[INFO] Server URL: http://localhost:{ORCHESTRATOR_PORT}")
    print(f"[INFO] Provider: AWS Bedrock")
    print(f"[INFO] Model: {BEDROCK_MODEL_ID}")
    print(f"[INFO] Region: {BEDROCK_REGION}")
    print(f"[INFO] Credentials: Using ~/.aws/credentials")
    print(f"[INFO] Prompt Caching: ENABLED")
    print(f"[INFO] AG-UI Protocol: ENABLED (via agent.to_ag_ui())")
    print(f"[INFO] A2A Middleware: READY TO RECEIVE TOOLS")
    print(f"[INFO] Parallel Tool Calls: DISABLED (Sequential execution)")
    print(f"[INFO] Message History: Fresh start for each request")
    print("=" * 80)
    print(f"[TIP] A2A middleware will inject send_message_to_a2a_agent tool")
    print(f"[TIP] Access the agent at: POST http://localhost:{ORCHESTRATOR_PORT}/")
    print("=" * 80)
    
    uvicorn.run(app, host="0.0.0.0", port=ORCHESTRATOR_PORT)