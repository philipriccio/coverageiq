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
from datetime import datetime
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
        except Exception as e:
            await db.rollback()
            print(f"Failed to update job progress: {e}")
    
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
        except Exception as e:
            await db.rollback()
            print(f"Failed to mark job as completed: {e}")
    
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
        except Exception as e:
            await db.rollback()
            print(f"Failed to mark job as failed: {e}")
    
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
        async with AsyncSessionLocal() as db:
            try:
                # Get job details
                result = await db.execute(
                    select(AnalysisJob).where(AnalysisJob.id == job_id)
                )
                job = result.scalar_one_or_none()
                
                if not job:
                    print(f"Job {job_id} not found")
                    return
                
                # Update to processing status
                await cls.update_progress(job_id, 5, JobStatus.PROCESSING, db)
                
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
                
            except Exception as e:
                error_msg = str(e)
                print(f"Job {job_id} failed: {error_msg}")
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
        - 25%: Script processed, sending to LLM
        - 50%: LLM analysis in progress
        - 75%: Processing LLM response
        - 100%: Complete
        """
        # Update progress: starting (5% already set)
        await cls.update_progress(job_id, 10, db=db)
        
        # Simulate progress during analysis
        # In a real implementation, the analysis service would emit progress events
        # Note: Don't pass db session - _simulate_progress_updates creates its own
        progress_task = asyncio.create_task(
            cls._simulate_progress_updates(job_id, 15, 60)
        )
        
        try:
            # Run the actual analysis
            report = await run_coverage_analysis(
                script_text=script_text,
                report_id=report_id,
                script_id=script_id,
                db=db,
                genre=genre,
                comps=comps,
                analysis_depth=analysis_depth
            )
            
            # Cancel progress simulation
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
            
            # Update progress: processing results
            await cls.update_progress(job_id, 75, db=db)
            await asyncio.sleep(0.5)  # Brief pause for UI effect
            
            # Final progress
            await cls.update_progress(job_id, 90, db=db)
            
            return report
            
        except Exception:
            # Cancel progress simulation on error
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass
            raise
    
    @classmethod
    async def _simulate_progress_updates(
        cls,
        job_id: str,
        start: int,
        end: int
    ):
        """Simulate progress updates during long-running operations.
        
        This provides visual feedback to users while the LLM processes.
        
        Note: Creates its own session to avoid concurrent access issues.
        """
        try:
            current = start
            while current < end:
                await asyncio.sleep(2)  # Update every 2 seconds
                current = min(end, current + 5)
                # Create new session for each update to avoid concurrent access
                async with AsyncSessionLocal() as session:
                    await cls._do_update_progress(job_id, current, None, session)
        except asyncio.CancelledError:
            # Expected when analysis completes
            pass
    
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
