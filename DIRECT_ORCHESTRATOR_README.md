# Direct Orchestrator Implementation

This document explains the direct orchestrator implementation that bypasses A2A middleware for testing and debugging purposes.

## Purpose

The direct orchestrator was created to isolate and test whether the AG-UI adapter tool call ID errors are specifically caused by A2A middleware integration issues. It allows the orchestrator to make direct HTTP calls to research and analysis agents, avoiding the protocol integration complexity.

## Architecture Comparison

### Original A2A Middleware Approach
```
User → Next.js UI → AG-UI Protocol → A2A Middleware → Orchestrator
                                          ↓
                                   A2A Protocol
                                          ↓
                           Research Agent ← → Analysis Agent
```

### Direct Orchestrator Approach
```
User → Next.js UI → AG-UI Protocol → Direct Orchestrator
                                          ↓
                                    Direct HTTP
                                          ↓
                           Research Agent ← → Analysis Agent
```

## Key Differences

| Aspect | A2A Middleware | Direct Orchestrator |
|--------|----------------|-------------------|
| Port | 9100 | 9103 |
| Communication | A2A Protocol | Direct HTTP |
| Tools | `send_message_to_a2a_agent` (injected) | `call_research_agent`, `call_analysis_agent` (built-in) |
| Dependencies | A2A middleware | httpx for HTTP calls |
| Debugging | Complex (protocol layer) | Simple (direct HTTP logs) |

## Setup and Usage

### 1. Environment Configuration

Add to your `.env` file:
```bash
# Enable direct orchestrator
USE_DIRECT_ORCHESTRATOR=true
ORCHESTRATOR_DIRECT_URL=http://localhost:9103
ORCHESTRATOR_DIRECT_PORT=9103

# AWS Bedrock (required)
BEDROCK_MODEL_ID=apac.anthropic.claude-sonnet-4-20250514-v1:0
BEDROCK_REGION=ap-northeast-2
```

### 2. Start Services

**Option A: Use Direct Orchestrator**
```bash
npm run dev-direct
```
This starts:
- Next.js UI (port 3000)
- **Direct Orchestrator** (port 9103)
- Research Agent (port 9101)
- Analysis Agent (port 9102)

**Option B: Compare with Original**
```bash
# Terminal 1: Original approach
npm run dev

# Terminal 2: Direct approach (after setting USE_DIRECT_ORCHESTRATOR=true)
npm run dev-direct
```

### 3. Test Agent Endpoints

Before testing the full flow, verify the research and analysis agents are responding:

```bash
# From project root
python test_agent_endpoints.py
```

Expected output:
```
✅ Research Agent Response: {"topic": "artificial intelligence", ...
✅ Analysis Agent Response: {"topic": "Artificial Intelligence", ...
✅ ALL TESTS PASSED - Both agents are responding correctly
```

### 4. Test in Browser

1. Open http://localhost:3000
2. Send a test query: "Research artificial intelligence"
3. Monitor logs in all terminals

**Expected behavior:**
- Direct orchestrator: Should work without tool call ID errors
- A2A middleware: May show tool call ID errors in logs

## Troubleshooting

### Common Issues

**1. Port 9103 already in use**
```bash
npm run shutdown  # Includes port 9103 cleanup
```

**2. AWS Bedrock connection issues**
```bash
# Check AWS credentials
aws configure list

# Verify AWS region is correct
echo $BEDROCK_REGION
```

**3. Agent endpoints not responding**
```bash
# Test individual agents
curl -X POST http://localhost:9101/invoke \
  -H "Content-Type: application/json" \
  -d '{"message":{"parts":[{"root":{"text":"test query"}}]}}'

curl -X POST http://localhost:9102/invoke \
  -H "Content-Type: application/json" \
  -d '{"message":{"parts":[{"root":{"text":"test data"}}]}}'
```

**4. Frontend not using direct orchestrator**
Check environment variable:
```bash
echo "USE_DIRECT_ORCHESTRATOR=$USE_DIRECT_ORCHESTRATOR"
```

Must be set to `true` (not `True` or `1`).

### Log Analysis

**Direct Orchestrator Logs:**
```
[HTTP] Calling Research Agent: artificial intelligence
[HTTP] Research Agent Response: {"topic": "artificial intelligence"...
[HTTP] Calling Analysis Agent with research data
[HTTP] Analysis Agent Response: {"topic": "Artificial Intelligence"...
```

**A2A Middleware Logs (problematic):**
```
Tool call with ID abc123 not found in the history.
ValueError: Tool call with ID abc123 not found in the history.
```

## Files Modified/Created

### New Files
- `agents/orchestrator_direct.py` - Direct orchestrator implementation
- `test_agent_endpoints.py` - HTTP endpoint testing script
- `DIRECT_ORCHESTRATOR_README.md` - This documentation

### Modified Files
- `package.json` - Added `dev-direct` and `dev:orchestrator-direct` scripts
- `app/api/copilotkit/route.ts` - Added conditional routing logic
- `.env.example` - Added new environment variables

## Testing Strategy

### Verification Steps

1. **Test Direct Connection Works**:
   - Set `USE_DIRECT_ORCHESTRATOR=true`
   - Run `npm run dev-direct`
   - Send query, verify no tool call ID errors

2. **Test Original Connection Shows Issue**:
   - Set `USE_DIRECT_ORCHESTRATOR=false`
   - Run `npm run dev`
   - Send same query, observe tool call ID errors

3. **Compare Results**:
   - If direct works but A2A fails → Issue is with A2A middleware
   - If both fail → Issue is with AG-UI protocol or deeper

### Success Criteria

- ✅ Complete workflow: Research → Analysis → Final Report
- ✅ No tool call ID errors in logs
- ✅ Structured JSON responses from both agents
- ✅ Frontend displays agent badges correctly

## Technical Implementation Notes

### HTTP Message Format

The A2A agents expect messages in this specific format:
```json
{
  "message": {
    "parts": [
      {
        "root": {
          "text": "Your query here"
        }
      }
    ]
  }
}
```

### Tool Implementation

```python
@tool
async def call_research_agent(ctx: RunContext, query: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{RESEARCH_AGENT_URL}/invoke",
            json={"message": {"parts": [{"root": {"text": query}}]}}
        )
        return response.text
```

### Sequential Execution

Both implementations use `parallel_tool_calls=False` to ensure:
1. Research agent called first
2. Analysis agent called with research results
3. Final report synthesized from both

## Next Steps

If direct orchestrator works but A2A middleware fails:

1. **Issue is confirmed** to be in A2A middleware ↔ AG-UI integration
2. **Temporary workaround**: Use direct orchestrator for development
3. **Upstream fix needed**: In A2A middleware to properly handle tool call history
4. **Alternative solutions**: Consider different agent communication patterns

If both approaches fail:
1. Issue is deeper in AG-UI protocol or Bedrock integration
2. Further investigation needed in AG-UI adapter message handling
3. May need to examine conversation history management