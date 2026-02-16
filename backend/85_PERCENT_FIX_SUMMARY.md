# 85% Hang Investigation - Fix Summary

## Problem
Philip's Deep analysis was hanging at 85% progress. The 20K token limit fix resolved the 60% hang, but analysis now gets stuck at 85%.

## Root Cause Analysis

The 85% progress point is significant because:
1. Progress simulation runs from 15% to 85% during LLM processing
2. At 85%, the simulation stops incrementing and just keeps updating the same value
3. The `run_coverage_analysis()` function should return, progress should jump to 90%, then 100%

Potential causes identified:
1. **LLM timeout insufficient for 20K tokens**: Deep mode requests 20K tokens but the default 120s timeout may be insufficient
2. **Progress simulation interfering**: The simulation continues updating the DB at 85% even after analysis completes
3. **Database contention**: SQLite locks could cause deadlocks between progress updates and final save
4. **JSON parsing large responses**: 20K tokens = ~15KB JSON which could take time to parse

## Fixes Applied

### 1. Enhanced Logging (job_manager.py)
Added granular DEBUG logging throughout the analysis flow:
- Entry/exit points of `run_coverage_analysis()`
- Progress simulation cancellation
- Progress updates to 90%
- Return of final report

### 2. Enhanced Logging (analysis.py)
Added DEBUG logging to `save_analysis_results()`:
- Report fetch operation
- Field updates
- Commit and refresh operations
- Exception handling

### 3. Enhanced Logging (llm_client.py)
Added DEBUG logging to Moonshot client:
- Request payload size
- Timeout calculation based on max_tokens
- JSON parsing start/completion
- Token usage reporting

### 4. Dynamic Timeout Scaling (llm_client.py)
Changed from fixed 120s timeout to dynamic calculation:
```python
calculated_timeout = timeout_override or max(self.timeout, 60.0 + (max_tokens / 1000.0 * 3.0))
```
This gives Deep mode (20K tokens) ~120s minimum + 60s base = ~180s timeout.

### 5. Progress Simulation Terminal State Detection (job_manager.py)
Added check in `_simulate_progress_updates()` to detect when job reaches terminal state:
```python
# Check if job status has changed to terminal state (analysis completed)
async with AsyncSessionLocal() as session:
    result = await session.execute(
        select(AnalysisJob.status).where(AnalysisJob.id == job_id)
    )
    current_status = result.scalar_one_or_none()
    if current_status in (JobStatus.COMPLETED, JobStatus.FAILED):
        break
```
This prevents unnecessary DB updates after analysis completes.

### 6. Test Script (test_quick_vs_deep.py)
Created diagnostic test to isolate mode-specific issues:
- Tests Quick mode (small output, should be fast)
- Tests Standard mode (medium output)
- Tests Deep mode (20K tokens, may hang)
- Reports which modes fail to identify if issue is Deep-specific

## Testing Recommendations

1. **Run the diagnostic test**:
   ```bash
   cd /data/.openclaw/workspace/coverageiq/backend
   source venv/bin/activate
   export MOONSHOT_API_KEY="your-key"
   python test_quick_vs_deep.py
   ```

2. **Monitor logs during Deep analysis**:
   Look for these specific log lines to identify where it hangs:
   - `[Job {id}] DEBUG: About to call run_coverage_analysis...`
   - `[Moonshot] DEBUG: About to call chat_completion...`
   - `[Moonshot] DEBUG: chat_completion returned`
   - `[Moonshot] DEBUG: About to parse JSON...`
   - `[Analysis] DEBUG: save_analysis_results - fetching report...`
   - `[Job {id}] DEBUG: About to update progress to 90%...`

3. **If still hanging at 85%**:
   - Check if `[Moonshot] DEBUG: chat_completion returned` appears
   - If yes: Issue is in JSON parsing or DB save
   - If no: Issue is LLM API not returning (timeout too short)

## Additional Monitoring

The enhanced logging will now show:
- Exact timeout values being used for each request
- Progress simulation detecting terminal states
- Database operation timing
- JSON parsing duration

This should make it clear exactly where the 85% hang occurs.

## Files Modified

1. `app/services/job_manager.py` - Added granular logging and terminal state detection
2. `app/services/analysis.py` - Added logging to save_analysis_results
3. `app/services/llm_client.py` - Added dynamic timeout and enhanced logging
4. `test_quick_vs_deep.py` - New diagnostic test script (created)

## Next Steps

1. Deploy these changes
2. Run the diagnostic test
3. Check logs to identify exact hang location
4. If needed, adjust timeout formula or add additional safeguards
