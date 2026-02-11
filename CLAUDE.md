# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Start All Services (Recommended)
```bash
npm run dev
```
This concurrently starts all 4 services:
- Next.js UI on http://localhost:3000
- Orchestrator agent on http://localhost:9100
- Research agent on http://localhost:9101
- Analysis agent on http://localhost:9102

### Individual Service Commands
```bash
npm run dev:ui           # Next.js frontend only
npm run dev:orchestrator # Orchestrator agent only
npm run dev:research     # Research agent only
npm run dev:analysis     # Analysis agent only
npm run build           # Build Next.js for production
npm run lint            # Lint frontend code
npm run shutdown         # Shutdown all service
```

### Python Environment Setup
```bash
cd agents
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Architecture Overview

This is a multi-agent A2A (Agent-to-Agent) application demonstrating inter-agent communication using two protocols:

### Core Components

**Frontend (Next.js + CopilotKit)**
- Main UI at `app/page.tsx`
- Chat component at `components/chat.tsx`
- A2A message visualization components in `components/a2a/`
- Connects to orchestrator via AG-UI Protocol

**Orchestrator Agent** (`agents/orchestrator.py`)
- Built with Pydantic AI + AWS Bedrock (Claude Sonnet)
- Receives user queries via AG-UI Protocol from frontend
- Coordinates specialized agents via A2A Protocol
- Sequential workflow: Research → Analysis → Final report
- Port 9100

**Research Agent** (`agents/research_agent.py`)
- Built with LangGraph + AWS Bedrock (Claude Sonnet)
- Gathers information on topics, returns structured JSON
- Communicates via A2A Protocol
- Port 9101

**Analysis Agent** (`agents/analysis_agent.py`)
- Built with Google ADK + Gemini
- Analyzes research findings, provides insights
- Communicates via A2A Protocol
- Port 9102

### Protocol Flow

```
User → Next.js UI → AG-UI Protocol → Orchestrator
                                        ↓
                                   A2A Protocol
                                        ↓
                            Research Agent → Analysis Agent
                                        ↓
                                Structured Response Back
```

## Key Files and Their Roles

**`app/api/copilotkit/route.ts`** - Critical integration point
- Sets up A2A Middleware that wraps the orchestrator
- Registers A2A agents (research, analysis)
- Injects `send_message_to_a2a_agent` tool into orchestrator
- Routes messages between agents transparently

**`agents/orchestrator.py`** - Main coordinator
- Uses `agent.to_ag_ui()` to create AG-UI compatible ASGI app
- System prompt defines sequential workflow (Research → Analysis)
- Receives `send_message_to_a2a_agent` tool from A2A middleware
- Must use `parallel_tool_calls=False` for sequential execution

**Agent Communication Pattern**
- All agents return structured JSON responses
- Research agent: `{topic, summary, findings[], sources}`
- Analysis agent: `{topic, overview, insights[], conclusion}`
- Frontend parses and displays these structures separately

## Environment Configuration

Required variables in `.env`:

**AWS Bedrock** (Orchestrator & Research Agent)
```
BEDROCK_MODEL_ID=apac.anthropic.claude-sonnet-4-20250514-v1:0
BEDROCK_REGION=ap-northeast-2
```
- Requires AWS credentials in `~/.aws/credentials`

**Google/Gemini** (Analysis Agent)
```
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

**Service URLs** (Optional - these are defaults)
```
ORCHESTRATOR_URL=http://localhost:9100
RESEARCH_AGENT_URL=http://localhost:9101
ANALYSIS_AGENT_URL=http://localhost:9102
```

## Development Considerations

### Adding New Agents
1. Create Python agent in `agents/` directory implementing A2A Protocol
2. Register in `app/api/copilotkit/route.ts` agentUrls array
3. Add npm script in `package.json` for the new agent
4. Update main `dev` script to include new agent in concurrently command
5. Update orchestrator instructions to include new agent in workflow

### Protocol Integration Notes
- **A2A Middleware** handles all agent-to-agent routing automatically
- Orchestrator doesn't need to understand A2A Protocol directly
- All A2A agents must implement the standard A2A server interface
- AG-UI Protocol connects frontend to orchestrator only

### Debugging Tips
- Check all 4 services are running on correct ports (3000, 9100-9102)
- Orchestrator logs show A2A tool injection and execution
- A2A agents have verbose logging for message handling
- Frontend displays agent badges showing message flow

### Architecture Patterns
- **Sequential Processing**: Orchestrator enforces Research → Analysis order
- **Structured Data**: All agents return validated JSON schemas
- **Protocol Separation**: AG-UI for UI communication, A2A for agent communication
- **Framework Diversity**: Demonstrates Pydantic AI, LangGraph, and Google ADK integration