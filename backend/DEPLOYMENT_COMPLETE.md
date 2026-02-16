# CoverageIQ 85% Hang Fix - DEPLOYMENT COMPLETE

## Executive Summary

**Status**: ✅ FIXES DEPLOYED TO PRODUCTION  
**Commit**: `53289cf`  
**Previous Issue**: Deep mode analysis hanging at 85% progress

---

## Root Cause Analysis (CONFIRMED)

The 85% hang was caused by a **token limit mismatch** in Deep mode:

### The Problem
1. **Deployed code used**: Fixed 8,000 max_tokens for ALL analysis modes
2. **Deep mode requires**: ~15,000-20,000 tokens for comprehensive JSON output
3. **Result**: Response truncated at 8,000 tokens (mid-JSON)
4. **JSON parsing failed**: But progress simulation kept running at 85%
5. **Job hung forever**: Never transitioned to FAILED or COMPLETED

### Why 85% Specifically?
- Progress simulation runs from 15% → 85% during LLM processing
- At 85%, simulation stops incrementing and just "touches" the timestamp
- If analysis fails at this point, simulation keeps running indefinitely
- Frontend shows "85%" forever with updating timestamps

---

## Fixes Applied (Now Deployed)

### 1. Dynamic Token Limits by Mode
```python
depth_token_limits = {
    "quick": 4000,      # Quick mode: smaller output
    "standard": 8000,   # Standard mode: default
    "deep": 20000       # Deep mode: large output for detailed analysis
}
```

### 2. Dynamic Timeout Scaling
```python
# Roughly 3 seconds per 1000 tokens + 60s base
calculated_timeout = 60.0 + (max_tokens / 1000.0 * 3.0)
# Deep mode: 60s + (20000/1000 * 3) = 60s + 60s = 120s minimum
```

### 3. Terminal State Detection
Progress simulation now checks if job reached COMPLETED/FAILED state and exits:
```python
if current_status in (JobStatus.COMPLETED, JobStatus.FAILED):
    print(f"Progress simulation detected terminal state, exiting")
    break
```

### 4. Enhanced DEBUG Logging
Added granular logging at every step:
- `[Job {id}] DEBUG: About to call run_coverage_analysis...`
- `[Moonshot] DEBUG: About to call chat_completion...`
- `[Moonshot] DEBUG: chat_completion returned`
- `[Job {id}] DEBUG: About to update progress to 90%...`

### 5. Better Truncation Detection
```python
if completion_tokens >= token_limit * 0.95:
    raise LLMError(
        f"JSON response appears truncated (used {completion_tokens}/{token_limit} tokens). "
        f"Consider increasing max_tokens for this analysis depth."
    )
```

---

## Test Plan for Philip

### Before You Test

1. **Clear any existing stuck jobs** (just to be safe):
   ```bash
   curl -X POST https://coverageiq-backend.onrender.com/api/coverage/admin/cleanup-stuck-jobs
   ```

2. **Check health endpoint** to verify deployment:
   ```bash
   curl https://coverageiq-backend.onrender.com/health
   ```
   Should return: `{"status":"healthy",...}`

### Test Procedure

#### Test 1: Quick Mode (Baseline)
1. Upload any TV pilot script
2. Select **Quick** analysis mode
3. Expected: Completes in 30-60 seconds
4. Check logs for: `Using max_tokens=4000 for quick analysis`

#### Test 2: Standard Mode
1. Upload same script
2. Select **Standard** analysis mode
3. Expected: Completes in 60-120 seconds
4. Check logs for: `Using max_tokens=8000 for standard analysis`

#### Test 3: Deep Mode (The Real Test)
1. Upload same script
2. Select **Deep** analysis mode
3. Expected: Completes in 120-300 seconds
4. Check logs for: `Using max_tokens=20000 for deep analysis`

### What to Look For

**✅ SUCCESS Indicators:**
- Progress reaches 90%, then 100%
- Report is generated with full content
- No hang at 85%
- Logs show: `run_coverage_analysis returned successfully`

**⚠️ If It Still Hangs:**
Check the Render logs for these specific lines to identify where:
```
# If you see this but NOT the next line → LLM API timeout issue
[Job {id}] DEBUG: About to call run_coverage_analysis...

# If you see this but NOT the next line → LLM not returning
[Moonshot] DEBUG: About to call chat_completion...

# If you see this but NOT the next line → JSON parsing issue
[Moonshot] DEBUG: chat_completion returned

# If you see this but NOT the next line → DB save issue
[Analysis] DEBUG: save_analysis_results - about to commit...
```

### If Deep Mode Still Fails

Run the diagnostic test locally:
```bash
cd /data/.openclaw/workspace/coverageiq/backend
source venv/bin/activate
export MOONSHOT_API_KEY="your-key"
python test_quick_vs_deep.py
```

This will test all three modes sequentially and report exactly which one fails.

---

## Deployment Verification

### Commits on GitHub
```
53289cf CRITICAL FIX: 85% hang - Dynamic token limits...
f261a11 Fix 60% hang issue: progress simulation limits...
```

### Files Changed
- `backend/app/services/analysis.py` - Depth-based token limits
- `backend/app/services/job_manager.py` - Terminal state detection + DEBUG logging
- `backend/app/services/llm_client.py` - Dynamic timeout + truncation detection

### Render Deployment
- Service: `coverageiq-backend`
- URL: https://coverageiq-backend.onrender.com
- Auto-deploy: Enabled (triggered by GitHub push)

---

## Rollback Plan (If Needed)

If issues arise, rollback to previous commit:
```bash
cd /data/.openclaw/workspace/coverageiq
git revert 53289cf
git push origin main
```

---

## Summary

**The 85% hang was caused by Deep mode responses being truncated at 8,000 tokens when they need 20,000 tokens.** The fixes are now deployed and include:

1. ✅ Dynamic token limits based on analysis depth
2. ✅ Dynamic timeout scaling (3s per 1K tokens)
3. ✅ Terminal state detection in progress simulation
4. ✅ Enhanced DEBUG logging throughout the pipeline
5. ✅ Better error messages for truncated responses

**Ready for testing!** Start with Quick mode, then Standard, then Deep. If Deep mode still hangs, the DEBUG logs will tell us exactly where.

---

*Audit completed: Feb 16, 2026*  
*Fix deployed: Commit 53289cf*
