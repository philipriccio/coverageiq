# Deep Mode Fix Summary

## Problem
Deep analysis mode was hanging at 60% because:
1. Deep mode prompt generates ~15-20K tokens of JSON output
2. max_tokens was hardcoded to 8000
3. Response was truncated mid-JSON
4. JSON parsing failed silently
5. Job hung without proper error handling

## Solution Applied

### 1. llm_client.py - Configurable max_tokens
- Added `max_tokens` parameter to both `MoonshotClient.analyze_script()` and `ClaudeClient.analyze_script()`
- Defaults to `DEFAULT_MAX_TOKENS` (8000) if not specified
- Logs token usage for debugging

### 2. llm_client.py - Better JSON Error Handling
- Added explicit truncation detection: checks if tokens used >= 95% of limit
- Clear error message when truncation occurs: "JSON response appears truncated..."
- Better logging throughout parsing process

### 3. analysis.py - Depth-Based Token Limits
- Added `depth_token_limits` mapping:
  - `quick`: 4000 tokens
  - `standard`: 8000 tokens  
  - `deep`: 20000 tokens
- Passes appropriate max_tokens based on analysis_depth
- Logs which token limit is being used

## Files Modified
- `/data/.openclaw/workspace/coverageiq/backend/app/services/llm_client.py`
- `/data/.openclaw/workspace/coverageiq/backend/app/services/analysis.py`

## Deployment
Service is running with `--reload` flag, so changes are automatically active.
No manual restart required.

## Testing Recommendation
Run a Deep mode analysis to verify the fix. The logs should now show:
- `[Analysis] Using max_tokens=20000 for deep analysis`
- `[Moonshot] Response tokens used: XXXX/20000`
- `[Moonshot] JSON parsed successfully`
