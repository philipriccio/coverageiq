"""Async job manager for coverage analysis.

Manages the lifecycle of async analysis jobs including:
- Job creation and queueing
- Background task execution
- Progress tracking and updates
- Result retrieval
"""
import asyncio
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import AnalysisJob, JobStatus, CoverageReport, ReportStatus
from app.database import AsyncSessionLocal
from app.services.analysis import run_coverage_analysis, AnalysisError


# In-memory store for active background tasks
_active_tasks: Dict[str, asyncio.Task] = {}


class JobManager:
    """Manages async analysis jobs."""
    
    @staticmethod
    def _hash_script_text(script_text: str) -> str:
        """Create a hash of script text for storage (NOT storing the actual text)."""
        return hashlib.sha256(script_text.encode()).hexdigest()
    
    @classmethod
    async def create_job(
        cls,
        script_id: str,
        script_text: str,
        report_id: str,
        db: AsyncSession,
        genre: Optional[str] = None,
        comps: Optional[list] = None,
        analysis_depth: str = "standard"
    ) -> AnalysisJob:
        """Create a new analysis job.
        
        Args:
            script_id: Script metadata UUID
            script_text: Full script text (hashed, not stored)
            report_id: Associated coverage report UUID
            db: Database session
            genre: Optional genre
            comps: Optional comparable series
            analysis_depth: Analysis depth level
            
        Returns:
            Created AnalysisJob
        """
        job_id = str(uuid.uuid4())
        script_hash = cls._hash_script_text(script_text)
        
        job = AnalysisJob(
            id=job_id,
            script_id=script_id,
            report_id=report_id,
            status=JobStatus.QUEUED,
            progress=0,
            script_text_hash=script_hash,
            genre=genre,
            comps=comps or [],
            analysis_depth=analysis_depth
        )
        
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        return job
    
    @classmethod
    async def get_job(cls, job_id: str, db: AsyncSession) -> Optional[AnalysisJob]:
        """Get a job by ID."""
        result = await db.execute(
            select(AnalysisJob).where(AnalysisJob.id == job_id)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def update_progress(
        cls,
        job_id: str,
        progress: int,
        status: Optional[JobStatus] = None,
        db: Optional[AsyncSession] = None
    ):
        """Update job progress.
        
        Args:
            job_id: Job UUID
            progress: Progress percentage (0-100)
            status: Optional new status
            db: Database session (creates new one if None)
        """
        if db is None:
            async with AsyncSessionLocal() as session:
                await cls._do_update_progress(job_id, progress, status, session)
        else:
            await cls._do_update_progress(job_id, progress, status, db)
    
    @classmethod
    async def _do_update_progress(
        cls,
        job_id: str,
        progress: int,
        status: Optional[JobStatus],
        db: AsyncSession
    ):
        """Internal method to update progress."""
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
            await db.rollback()
            raise  # Don't suppress cancellation
        except Exception as e:
            await db.rollback()
            print(f"[Job {job_id}] Failed to update progress: {type(e).__name__}: {e}")
            # Don't suppress - propagate to make failures visible
            raise
    
    @classmethod
    async def mark_completed(
        cls,
        job_id: str,
        db: Optional[AsyncSession] = None
    ):
        """Mark a job as completed."""
        if db is None:
            async with AsyncSessionLocal() as session:
                await cls._do_mark_completed(job_id, session)
        else:
            await cls._do_mark_completed(job_id, db)
    
    @classmethod
    async def _do_mark_completed(cls, job_id: str, db: AsyncSession):
        """Internal method to mark job completed."""
        try:
            result = await db.execute(
                select(AnalysisJob).where(AnalysisJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if job:
                job.status = JobStatus.COMPLETED
                job.progress = 100
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                await db.commit()
                print(f"[Job {job_id}] Marked as completed")
        except asyncio.CancelledError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            print(f"[Job {job_id}] Failed to mark completed: {type(e).__name__}: {e}")
            raise
    
    @classmethod
    async def mark_failed(
        cls,
        job_id: str,
        error_message: str,
        db: Optional[AsyncSession] = None
    ):
        """Mark a job as failed."""
        if db is None:
            async with AsyncSessionLocal() as session:
                await cls._do_mark_failed(job_id, error_message, session)
        else:
            await cls._do_mark_failed(job_id, error_message, db)
    
    @classmethod
    async def _do_mark_failed(cls, job_id: str, error_message: str, db: AsyncSession):
        """Internal method to mark job failed."""
        try:
            result = await db.execute(
                select(AnalysisJob).where(AnalysisJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if job:
                job.status = JobStatus.FAILED
                job.error_message = error_message
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                await db.commit()
                print(f"[Job {job_id}] Marked as failed: {error_message[:100]}")
        except asyncio.CancelledError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            print(f"[Job {job_id}] Failed to mark failed: {type(e).__name__}: {e}")
            raise
    
    @classmethod
    def start_background_task(
        cls,
        job_id: str,
        script_text: str,
        report_id: str
    ):
        """Start a background task for analysis.
        
        Args:
            job_id: Job UUID
            script_text: Full script text
            report_id: Report UUID
        """
        task = asyncio.create_task(
            cls._run_analysis_job(job_id, script_text, report_id)
        )
        _active_tasks[job_id] = task
        
        # Clean up task when done
        task.add_done_callback(lambda t: _active_tasks.pop(job_id, None))
    
    @classmethod
    async def _run_analysis_job(
        cls,
        job_id: str,
        script_text: str,
        report_id: str
    ):
        """Background task to run analysis with progress updates.
        
        Args:
            job_id: Job UUID
            script_text: Full script text
            report_id: Report UUID
        """
        print(f"[Job {job_id}] Starting background analysis task")
        
        async with AsyncSessionLocal() as db:
            try:
                # Get job details
                result = await db.execute(
                    select(AnalysisJob).where(AnalysisJob.id == job_id)
                )
                job = result.scalar_one_or_none()
                
                if not job:
                    print(f"[Job {job_id}] Job not found")
                    return
                
                # Check if job is too old (stuck from previous attempt)
                job_age = datetime.utcnow() - job.created_at
                if job_age > timedelta(minutes=10):
                    error_msg = f"Job exceeded maximum age ({job_age.total_seconds()/60:.1f} minutes)"
                    print(f"[Job {job_id}] {error_msg}")
                    await cls.mark_failed(job_id, error_msg, db)
                    return
                
                # Check if job is already in terminal state
                if job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    print(f"[Job {job_id}] Job already in terminal state: {job.status.value}")
                    return
                
                # Update to processing status
                await cls.update_progress(job_id, 5, JobStatus.PROCESSING, db)
                print(f"[Job {job_id}] Updated to PROCESSING status")
                
                # Run analysis with progress callbacks
                report = await cls._run_analysis_with_progress(
                    script_text=script_text,
                    report_id=report_id,
                    script_id=job.script_id,
                    job_id=job_id,
                    db=db,
                    genre=job.genre,
                    comps=job.comps,
                    analysis_depth=job.analysis_depth
                )
                
                # Mark as completed
                await cls.mark_completed(job_id, db)
                print(f"[Job {job_id}] Analysis completed successfully")
                
            except asyncio.CancelledError:
                print(f"[Job {job_id}] Job was cancelled")
                await cls.mark_failed(job_id, "Job was cancelled", db)
                raise  # Re-raise to propagate cancellation
            except AnalysisError as e:
                error_msg = f"Analysis failed: {str(e)}"
                print(f"[Job {job_id}] {error_msg}")
                await cls.mark_failed(job_id, error_msg, db)
            except Exception as e:
                error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
                print(f"[Job {job_id}] {error_msg}")
                await cls.mark_failed(job_id, error_msg, db)
    
    @classmethod
    async def _run_analysis_with_progress(
        cls,
        script_text: str,
        report_id: str,
        script_id: str,
        job_id: str,
        db: AsyncSession,
        genre: Optional[str],
        comps: Optional[list],
        analysis_depth: str
    ) -> CoverageReport:
        """Run analysis with progress updates.
        
        Progress stages:
        - 5%: Starting analysis
        - 10%: Script processed
        - 15-85%: LLM analysis in progress (simulated)
        - 90%: Processing results
        - 100%: Complete
        """
        # Update progress: starting (5% already set)
        await cls.update_progress(job_id, 10, db=db)
        
        # Simulate progress during analysis - now runs up to 85%
        # This provides visual feedback while the LLM processes
        progress_task = asyncio.create_task(
            cls._simulate_progress_updates(job_id, 15, 85, interval=3)
        )
        
        try:
            # Run the actual analysis with a hard timeout
            # This prevents infinite hangs if the LLM client misbehaves
            print(f"[Job {job_id}] Starting analysis with 300s timeout...")
            report = await asyncio.wait_for(
                run_coverage_analysis(
                    script_text=script_text,
                    report_id=report_id,
                    script_id=script_id,
                    db=db,
                    genre=genre,
                    comps=comps,
                    analysis_depth=analysis_depth
                ),
                timeout=300.0  # 5 minute hard timeout
            )
            print(f"[Job {job_id}] Analysis completed successfully")
            
            # Cancel progress simulation
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
            
            # Update progress: processing results
            await cls.update_progress(job_id, 90, db=db)
            await asyncio.sleep(0.1)  # Brief pause for UI effect
            
            return report
            
        except asyncio.TimeoutError:
            # Cancel progress simulation on timeout
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
            print(f"[Job {job_id}] Analysis timed out after 300s")
            raise AnalysisError("Analysis timed out after 5 minutes. The LLM service may be experiencing issues.")
            
        except Exception as e:
            # Cancel progress simulation on error
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
            print(f"[Job {job_id}] Analysis failed: {type(e).__name__}: {e}")
            raise
    
    @classmethod
    async def _simulate_progress_updates(
        cls,
        job_id: str,
        start: int,
        end: int,
        interval: float = 2.0,
        max_duration: float = 300.0
    ):
        """Simulate progress updates during long-running operations.
        
        This provides visual feedback to users while the LLM processes.
        
        Args:
            job_id: Job UUID
            start: Starting progress percentage
            end: Ending progress percentage  
            interval: Seconds between updates (default 2.0)
            max_duration: Maximum time to run simulation (default 300s = 5 min)
            
        Note: Creates its own session to avoid concurrent access issues.
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            current = start
            # Calculate increment to reach end in reasonable time
            # Aim for about 30 updates max to reach end
            total_range = end - start
            increment = max(1, total_range // 30)
            
            while current < end:
                # Check if we've exceeded max duration
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > max_duration:
                    print(f"[Job {job_id}] Progress simulation reached max duration at {current}%")
                    break
                
                await asyncio.sleep(interval)
                current = min(end, current + increment)
                # Create new session for each update to avoid concurrent access
                async with AsyncSessionLocal() as session:
                    await cls._do_update_progress(job_id, current, None, session)
                    
            # Keep updating at end value for a limited time (not infinite)
            # This prevents progress from appearing "stuck" at end
            # but ensures we don't run forever if cancellation fails
            max_end_updates = 30  # ~60 seconds of end-state updates at interval*2
            end_update_count = 0
            
            while end_update_count < max_end_updates:
                # Check if we've exceeded max duration
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > max_duration:
                    print(f"[Job {job_id}] Progress simulation max duration reached")
                    break
                
                await asyncio.sleep(interval * 2)
                # Just touch the updated_at timestamp to show activity
                async with AsyncSessionLocal() as session:
                    await cls._do_update_progress(job_id, end, None, session)
                end_update_count += 1
            
            print(f"[Job {job_id}] Progress simulation completed after {end_update_count} end-state updates")
                    
        except asyncio.CancelledError:
            # Expected when analysis completes
            print(f"[Job {job_id}] Progress simulation cancelled as expected")
            raise  # Re-raise to properly signal cancellation
        except Exception as e:
            print(f"[Job {job_id}] Progress simulation error: {type(e).__name__}: {e}")
            # Don't suppress - let it propagate for visibility
            raise
    
    @classmethod
    def cancel_job(cls, job_id: str) -> bool:
        """Cancel an active job.
        
        Args:
            job_id: Job UUID
            
        Returns:
            True if job was cancelled, False if not found or already done
        """
        task = _active_tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            return True
        return False


# Singleton instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get or create the job manager singleton."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
