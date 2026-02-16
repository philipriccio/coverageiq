# CoverageIQ 60% Hang Issue - Comprehensive Audit Report

**Date:** February 16, 2026  
**Auditor:** Subagent Analysis  
**Status:** CRITICAL ISSUES IDENTIFIED

---

## Executive Summary

After thorough analysis of the CoverageIQ codebase, deployment history, and debugging logs, I have identified **multiple root causes** for the persistent 60% hang issue. The problem is not a single bug but a combination of architectural gaps, timeout mishandling, and race conditions in the async job queue system.

---

## Part 1: Current Flow Analysis (Job Start → 60% → Completion)

### Normal Flow:
```
1. POST /generate-async
   └── Create report (PROCESSING status)
   └── Create analysis job (QUEUED status, 0% progress)
   └── Start background task

2. Background Task (_run_analysis_job)
   └── Update progress to 5%, status PROCESSING
   └── Call _run_analysis_with_progress
       └── Update progress to 10%
       └── Start progress simulation task (15% → 85%)
       └── Call run_coverage_analysis with 300s timeout
           └── Send to Moonshot/Claude LLM
           └── Parse response
           └── Save results to database
       └── Cancel progress simulation
       └── Update progress to 90%
       └── Return report
   └── Mark job COMPLETED (100%)

3. Frontend polls every 2 seconds
   └── GET /jobs/{job_id}/status
   └── Returns current progress
```

### Where It Hangs at 60%:

The 60% hang occurs when:
1. Progress simulation is running (somewhere between 15-85%)
2. The actual LLM analysis is hanging or taking longer than expected
3. The 300-second timeout fails to properly cancel the hung operation
4. The progress simulation continues indefinitely in its `while True` loop at 85%

---

## Part 2: ALL Potential Causes of the 60% Hang

### 🔴 CRITICAL ISSUE #1: Infinite Progress Simulation Loop
**File:** `app/services/job_manager.py`  
**Line:** ~365-375 in `_simulate_progress_updates`

```python
# Keep updating at end value to show activity until cancelled
# This prevents progress from appearing "stuck" at end
while True:
    await asyncio.sleep(interval * 2)
    # Just touch the updated_at timestamp to show activity
    async with AsyncSessionLocal() as session:
        await cls._do_update_progress(job_id, end, None, session)
```

**Problem:** Once progress reaches 85%, this `while True` loop runs forever until the task is cancelled. If the analysis hangs and the cancellation doesn't work properly, this loop continues indefinitely, keeping the job at 85% (or wherever it was) forever.

**Impact:** HIGH - This is the primary visible symptom

---

### 🔴 CRITICAL ISSUE #2: Timeout Doesn't Cancel Underlying Operation
**File:** `app/services/job_manager.py`  
**Line:** ~240-255 in `_run_analysis_with_progress`

```python
report = await asyncio.wait_for(
    run_coverage_analysis(...),
    timeout=300.0  # 5 minute hard timeout
)
```

**Problem:** `asyncio.wait_for()` raises `TimeoutError` after 300 seconds, BUT it does NOT cancel the underlying `run_coverage_analysis` coroutine. The LLM request continues running in the background, and more importantly, the progress simulation's infinite loop continues.

The exception handler tries to cancel the progress task:
```python
progress_task.cancel()
try:
    await progress_task
except asyncio.CancelledError:
    pass
```

But if this cancellation fails or hangs, the progress simulation keeps running.

**Impact:** HIGH - Analysis continues consuming resources after timeout

---

### 🔴 CRITICAL ISSUE #3: Missing Exception Handling in Progress Simulation
**File:** `app/services/job_manager.py`  
**Lines:** 335-375

The `_simulate_progress_updates` method has bare exception handling:
```python
except Exception as e:
    # Silently ignores ALL other exceptions
    pass
```

This means if database operations fail, the error is swallowed and the simulation continues (or exits without proper cleanup).

**Impact:** MEDIUM - Silent failures hide root causes

---

### 🔴 CRITICAL ISSUE #4: Database Session Concurrency Issues
**File:** `app/services/job_manager.py`  
**Multiple locations**

The progress simulation creates new database sessions for each update:
```python
async with AsyncSessionLocal() as session:
    await cls._do_update_progress(job_id, current, None, session)
```

While `NullPool` helps with SQLite, there's still a race condition:
1. Main analysis holds a database session
2. Progress simulation creates new sessions repeatedly
3. If SQLite locks, the progress update hangs
4. Since exceptions are swallowed, the hang is invisible

**Impact:** MEDIUM - Can cause silent hangs

---

### 🟡 MODERATE ISSUE #5: LLM Client Timeout Configuration
**File:** `app/services/llm_client.py`  
**Line:** ~65 and ~395

Moonshot client timeout: 120 seconds  
Analysis timeout: 300 seconds

For chunked analysis, this creates a problem:
- Script split into 3 chunks
- Each chunk takes 100+ seconds
- Total time > 300 seconds
- The 300s timeout fires, but chunks may be mid-processing

The client-level timeout should be shorter than the operation-level timeout to ensure proper cascading.

**Impact:** MEDIUM - Can cause premature timeouts or resource waste

---

### 🟡 MODERATE ISSUE #6: No Job-Level Timeout Tracking
**File:** `app/services/job_manager.py`

There's no tracking of when a job started vs. current time. The job relies entirely on `asyncio.wait_for()`, which can fail if the event loop is blocked.

A job-level timeout would be more robust:
```python
if datetime.utcnow() - job.created_at > timedelta(minutes=5):
    await cls.mark_failed(job_id, "Job exceeded maximum runtime")
```

**Impact:** MEDIUM - No fallback if asyncio.wait_for fails

---

### 🟡 MODERATE ISSUE #7: Missing Stuck Job Detection
**File:** `app/services/job_manager.py`

There's no mechanism to detect and recover jobs that are:
- In PROCESSING state for > 10 minutes
- Making progress updates but never completing
- Consuming resources indefinitely

**Impact:** LOW-MEDIUM - Manual intervention required

---

### 🟡 MODERATE ISSUE #8: Claude Model ID Inconsistency
**File:** `app/services/analysis.py`  
**Line:** ~145

```python
model_used = "claude-3-5-sonnet-20241022"  # Hardcoded after successful call
```

But in `llm_client.py`:
```python
MODEL_CLAUDE_SONNET = "claude-sonnet-4-5"  # What was actually called
```

This is a mismatch. The model ID saved to the database doesn't match what was actually used.

**Impact:** LOW - Logging inaccuracy

---

## Part 3: Gaps in Error Handling and Logging

### Gap #1: No Structured Logging
All logging uses `print()` statements. There's no:
- Log levels (DEBUG, INFO, ERROR)
- Structured format (JSON)
- Request correlation IDs
- Timestamp standardization

This makes debugging production issues extremely difficult.

### Gap #2: Swallowed Exceptions
Multiple locations catch exceptions and either:
- Print and continue (losing stack traces)
- Silently pass (hiding errors entirely)

Examples:
- `job_manager.py:mark_failed()` - catches all exceptions, prints, continues
- `job_manager.py:_do_update_progress()` - catches all exceptions, rolls back, continues
- `job_manager.py:_simulate_progress_updates()` - catches all exceptions, passes

### Gap #3: No Request Tracing
When a job hangs at 60%, there's no way to know:
- Which LLM was being called
- How long the current operation has been running
- Whether it's waiting for network, database, or processing

### Gap #4: Missing Health Checks
The `/health` endpoint only returns static data:
```python
@app.get("/health")
def health():
    return {"status": "healthy", ...}  # Always healthy!
```

It doesn't check:
- Database connectivity
- LLM API availability
- Queue depth / stuck jobs

---

## Part 4: Specific Fixes for Each Issue

### Fix #1: Add Maximum Duration to Progress Simulation (CRITICAL)

```python
@classmethod
async def _simulate_progress_updates(
    cls,
    job_id: str,
    start: int,
    end: int,
    interval: float = 2.0,
    max_duration: float = 300.0  # Add this parameter
):
    """Simulate progress updates during long-running operations."""
    start_time = asyncio.get_event_loop().time()
    
    try:
        current = start
        total_range = end - start
        increment = max(1, total_range // 30)
        
        while current < end:
            # Check if we've exceeded max duration
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_duration:
                print(f"[Job {job_id}] Progress simulation exceeded max duration")
                break
                
            await asyncio.sleep(interval)
            current = min(end, current + increment)
            async with AsyncSessionLocal() as session:
                await cls._do_update_progress(job_id, current, None, session)
        
        # At end value, only update for a limited time (not infinite)
        max_end_updates = 10  # ~20 seconds of end-state updates
        end_update_count = 0
        
        while end_update_count < max_end_updates:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_duration:
                break
                
            await asyncio.sleep(interval * 2)
            async with AsyncSessionLocal() as session:
                await cls._do_update_progress(job_id, end, None, session)
            end_update_count += 1
                
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[Job {job_id}] Progress simulation error: {e}")
        # Don't suppress - let it propagate for visibility
        raise
```

### Fix #2: Properly Cancel LLM Operations on Timeout (CRITICAL)

The LLM clients need to accept an `asyncio.Event` or similar cancellation mechanism:

```python
# In llm_client.py - MoonshotClient.chat_completion
async def chat_completion(
    self,
    messages: List[Dict[str, str]],
    cancellation_event: Optional[asyncio.Event] = None,  # Add this
    ...
) -> Dict[str, Any]:
    
    # During the request, periodically check for cancellation
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        try:
            # Use a shielded task that can be cancelled
            request_task = asyncio.create_task(
                client.post(f"{self.BASE_URL}/chat/completions", ...)
            )
            
            # Wait for either completion or cancellation
            done, pending = await asyncio.wait(
                [request_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            if cancellation_event and cancellation_event.is_set():
                request_task.cancel()
                try:
                    await request_task
                except asyncio.CancelledError:
                    pass
                raise asyncio.CancelledError("Request cancelled by timeout")
            
            response = await request_task
            ...
```

### Fix #3: Add Job-Level Timeout Check

```python
@classmethod
async def _run_analysis_job(cls, job_id: str, script_text: str, report_id: str):
    async with AsyncSessionLocal() as db:
        try:
            # Get job and check if it's already exceeded max runtime
            result = await db.execute(
                select(AnalysisJob).where(AnalysisJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                return
            
            # Check for stuck jobs
            max_job_age = timedelta(minutes=10)
            if datetime.utcnow() - job.created_at > max_job_age:
                await cls.mark_failed(job_id, "Job exceeded maximum age", db)
                return
            
            # Continue with normal processing...
```

### Fix #4: Better Exception Handling with Structured Logging

Replace all bare `except Exception` with specific handling:

```python
import logging
import traceback

logger = logging.getLogger(__name__)

@classmethod
async def _do_update_progress(cls, job_id: str, progress: int, status: Optional[JobStatus], db: AsyncSession):
    try:
        result = await db.execute(
            select(AnalysisJob).where(AnalysisJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if job:
            job.progress = min(100, max(0, progress))
            if status:
                job.status = status
            job.updated_at = datetime.utcnow()
            await db.commit()
    except asyncio.CancelledError:
        raise  # Don't suppress cancellation
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to update job progress: {e}", exc_info=True)
        # Re-raise to make failures visible
        raise
```

### Fix #5: Add Stuck Job Recovery Endpoint

```python
@router.post("/admin/cleanup-stuck-jobs")
async def cleanup_stuck_jobs(db: AsyncSession = Depends(get_db)):
    """Admin endpoint to mark stuck jobs as failed."""
    stuck_threshold = datetime.utcnow() - timedelta(minutes=10)
    
    result = await db.execute(
        select(AnalysisJob).where(
            AnalysisJob.status.in_([JobStatus.QUEUED, JobStatus.PROCESSING]),
            AnalysisJob.updated_at < stuck_threshold
        )
    )
    stuck_jobs = result.scalars().all()
    
    for job in stuck_jobs:
        await JobManager.mark_failed(
            job.id, 
            "Job marked as failed due to timeout (cleanup)", 
            db
        )
    
    return {"cleaned_up": len(stuck_jobs), "job_ids": [j.id for j in stuck_jobs]}
```

### Fix #6: Fix Claude Model ID Consistency

```python
# In analysis.py, line ~145
model_used = ClaudeClient.MODEL_CLAUDE_SONNET  # Use constant instead of hardcoded string
```

### Fix #7: Add Enhanced Health Check

```python
@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Health check with dependency verification."""
    status = {"status": "healthy", "version": "0.2.0"}
    
    # Check database
    try:
        await db.execute("SELECT 1")
        status["database"] = "connected"
    except Exception as e:
        status["database"] = f"error: {e}"
        status["status"] = "degraded"
    
    # Check for stuck jobs
    try:
        stuck_threshold = datetime.utcnow() - timedelta(minutes=10)
        result = await db.execute(
            select(AnalysisJob).where(
                AnalysisJob.status.in_([JobStatus.QUEUED, JobStatus.PROCESSING]),
                AnalysisJob.updated_at < stuck_threshold
            )
        )
        stuck_count = len(result.scalars().all())
        status["stuck_jobs"] = stuck_count
        if stuck_count > 0:
            status["status"] = "degraded"
    except Exception as e:
        status["stuck_jobs_check"] = f"error: {e}"
    
    return status
```

---

## Part 5: Immediate Actions for Philip

### Action 1: Deploy Emergency Fix (Progress Simulation Limit)
This is the most critical fix - it prevents the infinite loop.

### Action 2: Add Monitoring
Set up a cron job or periodic task to call the cleanup endpoint every 5 minutes.

### Action 3: Enable Debug Logging
Add `SQL_ECHO=true` and detailed request logging temporarily to capture what's happening when hangs occur.

### Action 4: Reduce Analysis Timeout
Change the 300-second timeout to 180 seconds (3 minutes) to fail faster and free resources.

---

## Summary Table

| Issue | Severity | File | Line(s) | Fix Complexity |
|-------|----------|------|---------|----------------|
| Infinite progress loop | CRITICAL | job_manager.py | 365-375 | Low |
| Timeout doesn't cancel LLM | CRITICAL | job_manager.py | 240-255 | Medium |
| Swallowed exceptions | HIGH | job_manager.py | Multiple | Low |
| DB session concurrency | MEDIUM | job_manager.py | 340-360 | Medium |
| LLM timeout mismatch | MEDIUM | llm_client.py | 65, 395 | Low |
| No job-level timeout | MEDIUM | job_manager.py | 200+ | Low |
| No stuck job detection | LOW | job_manager.py | N/A | Medium |
| Model ID mismatch | LOW | analysis.py | 145 | Low |

---

## Root Cause Summary

The 60% hang is primarily caused by:

1. **The progress simulation's infinite `while True` loop** that continues indefinitely when the analysis hangs
2. **The 300-second timeout not properly cancelling** the underlying LLM operations
3. **Swallowed exceptions** that hide the true cause of failures

When these three issues combine:
- Analysis hangs at the LLM level (network issue, slow response, etc.)
- The 300s timeout fires but doesn't stop the LLM call
- Progress simulation continues in its infinite loop
- Frontend keeps seeing "progress" (timestamp updates) at ~60-85%
- Job never completes or fails

**Recommended Priority:**
1. Deploy Fix #1 (progress simulation limit) immediately
2. Add better logging to identify specific hang causes
3. Implement Fix #2 (proper cancellation) for long-term stability

---

*End of Audit Report*
