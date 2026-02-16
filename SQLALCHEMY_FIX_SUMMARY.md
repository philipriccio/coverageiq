# SQLAlchemy Concurrent Operations Fix

## Issue
**Error:** `InvalidStateChangeError: This session is provisioning a new connection; concurrent operations are not permitted (Background on this error at: https://sqlalche.me/e/20/isce)`

## Root Cause
The error occurred in the CoverageIQ backend (`coverageiq/backend/app/services/job_manager.py`). The `_run_analysis_job` method was passing the same SQLAlchemy `AsyncSession` to multiple concurrent operations:

1. The main analysis coroutine (`run_coverage_analysis`) was using the session
2. A background progress simulation task (`_simulate_progress_updates`) was ALSO using the same session

SQLAlchemy 2.0's async sessions are **not thread-safe** and **cannot be shared across concurrent coroutines**. When two coroutines try to use the same session simultaneously, SQLAlchemy raises the ISCE (InvalidStateChangeError).

## The Fix

### File Modified
`/data/.openclaw/workspace/coverageiq/backend/app/services/job_manager.py`

### Changes Made

1. **Modified `_simulate_progress_updates` method** to create its own session instead of receiving one as a parameter:
   ```python
   # Before:
   async def _simulate_progress_updates(cls, job_id, start, end, db):
       # ... uses the passed-in db session
       await cls.update_progress(job_id, current, db=db)
   
   # After:
   async def _simulate_progress_updates(cls, job_id, start, end):
       # Creates its own session
       async with AsyncSessionLocal() as session:
           await cls._do_update_progress(job_id, current, None, session)
   ```

2. **Updated the call site** in `_run_analysis_with_progress` to not pass the session:
   ```python
   # Before:
   progress_task = asyncio.create_task(
       cls._simulate_progress_updates(job_id, 15, 60, db)
   )
   
   # After:
   progress_task = asyncio.create_task(
       cls._simulate_progress_updates(job_id, 15, 60)
   )
   ```

## Why This Fixes the Issue

Each concurrent operation now has its own isolated database session:
- The main analysis coroutine uses the session created in `_run_analysis_job`
- The progress simulation task creates a new session for each update

This prevents the "concurrent operations are not permitted" error because:
1. Sessions are never shared between concurrent coroutines
2. Each session is properly managed within its own async context manager
3. SQLAlchemy's session state machine remains valid

## Testing

A test script was created to verify the fix:
```bash
cd /data/.openclaw/workspace/coverageiq/backend
./venv/bin/python test_concurrent_session_fix.py
```

Result: ✓ All tests passed!

## Deployment

To deploy this fix to the live CoverageIQ backend:

1. Commit the changes:
   ```bash
   cd /data/.openclaw/workspace/coverageiq
   git add backend/app/services/job_manager.py
   git commit -m "Fix SQLAlchemy concurrent session error in job_manager.py"
   ```

2. Push to GitHub (triggers auto-deploy to Render):
   ```bash
   git push origin main
   ```

3. Verify deployment:
   - Check Render dashboard: https://dashboard.render.com/web/srv-d696u314tr6s73cgpft0
   - Test the `/health` endpoint: `curl https://coverageiq-backend.onrender.com/health`

## Prevention

To prevent similar issues in the future:

1. **Never share async sessions** between concurrent coroutines
2. **Always use `async with AsyncSessionLocal()`** to create new sessions
3. **Use FastAPI's `Depends(get_db)`** for request-scoped sessions in endpoints
4. **Review any `asyncio.create_task()` calls** that might use shared resources

## References

- SQLAlchemy ISCE Error Documentation: https://sqlalche.me/e/20/isce
- SQLAlchemy Async Session Documentation: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
