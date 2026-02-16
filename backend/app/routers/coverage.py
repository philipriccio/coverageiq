"""Coverage report generation endpoints."""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import CoverageReport, ScriptMetadata, ReportStatus, Recommendation
from app.services.analysis import run_coverage_analysis, AnalysisError
from app.services.google_docs_export import (
    get_google_docs_exporter, GoogleDocsExportError
)
from app.services.pdf_export import get_pdf_exporter, PDFExportError

router = APIRouter(prefix="/api/coverage", tags=["coverage"])


class CoverageRequest(BaseModel):
    """Request to start coverage analysis."""
    script_id: str
    genre: Optional[str] = None
    comps: Optional[List[str]] = None  # Comparable films
    analysis_depth: str = "standard"  # quick, standard, deep


class Subscores(BaseModel):
    """Five category subscores (/10 each = /50 total)."""
    concept: int  # Concept & Premise
    structure: int  # Structure & Pacing
    character: int  # Character & Dialogue
    market: int  # Market Viability
    writing: int  # Writing Quality & Voice


class EvidenceQuote(BaseModel):
    """A short evidence quote from the script."""
    quote: str  # 1-2 lines max
    page: int
    context: Optional[str] = None


class CoverageReportResponse(BaseModel):
    """Full coverage report response."""
    report_id: str
    script_id: str
    script_title: Optional[str]
    
    # Analysis configuration
    genre: Optional[str]
    comps: Optional[List[str]]
    analysis_depth: str
    
    # Status
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    
    # Scores
    subscores: Optional[dict]
    total_score: Optional[int]  # /50
    recommendation: Optional[str]  # Pass, Consider, Recommend
    
    # Report content
    logline: Optional[str]
    synopsis: Optional[str]
    overall_comments: Optional[str]
    strengths: List[str]
    weaknesses: List[str]
    character_notes: Optional[str]
    structure_analysis: Optional[str]
    market_positioning: Optional[str]
    evidence_quotes: List[EvidenceQuote]
    
    model_used: str


class CoverageListResponse(BaseModel):
    """Simplified report for list views."""
    report_id: str
    script_id: str
    script_title: Optional[str]
    status: str
    total_score: Optional[int]
    recommendation: Optional[str]
    created_at: datetime


async def _get_script_text(script_id: str) -> str:
    """Retrieve script text for analysis.
    
    In the actual implementation, this would retrieve from a temporary
    storage or cache. For now, we assume the text is passed through or
    retrieved from the upload session.
    
    Args:
        script_id: Script UUID
        
    Returns:
        Script text content
    """
    # TODO: Implement script text retrieval from memory/cache
    # For testing, this will be handled by the test endpoint
    raise NotImplementedError("Script text retrieval not implemented")


@router.post("/generate", response_model=CoverageListResponse)
async def generate_coverage(
    request: CoverageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start coverage analysis for a script.
    
    This creates a report record with status 'processing' and queues the analysis
    to run in the background. Poll the GET endpoint to check for completion.
    
    ## Scoring System
    - 5 categories × /10 = /50 total
    - **Pass** (0-24): Not ready for consideration
    - **Consider** (25-37): Shows promise with reservations  
    - **Recommend** (38-50): Strong contender, pursue immediately
    """
    # Verify script exists
    result = await db.execute(
        select(ScriptMetadata).where(ScriptMetadata.id == request.script_id)
    )
    script = result.scalar_one_or_none()
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Create report record
    report_id = str(uuid.uuid4())
    report = CoverageReport(
        id=report_id,
        script_id=request.script_id,
        genre=request.genre,
        comps=request.comps or [],
        analysis_depth=request.analysis_depth,
        status=ReportStatus.PROCESSING,
        subscores={},
        model_used="kimi-k2.5"  # Default to Kimi
    )
    
    db.add(report)
    await db.commit()
    
    # Queue background analysis
    # TODO: Implement with Celery or similar
    # For now, analysis is run synchronously via the test endpoint
    
    return CoverageListResponse(
        report_id=report_id,
        script_id=request.script_id,
        script_title=script.title,
        status=report.status.value,
        total_score=None,
        recommendation=None,
        created_at=report.created_at
    )


class SyncCoverageRequest(BaseModel):
    """Request for synchronous coverage generation."""
    script_id: str
    script_text: str  # Script content for processing
    genre: Optional[str] = None
    comps: Optional[List[str]] = None
    analysis_depth: str = "standard"


@router.post("/generate-sync", response_model=CoverageReportResponse)
async def generate_coverage_sync(
    request: SyncCoverageRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate coverage analysis synchronously (for testing).
    
    This endpoint runs analysis immediately and returns the full results.
    For production, use the async /generate endpoint.
    
    ## Scoring System
    - 5 categories × /10 = /50 total
    - **Pass** (0-24): Not ready for consideration
    - **Consider** (25-37): Shows promise with reservations  
    - **Recommend** (38-50): Strong contender, pursue immediately
    """
    # Verify script exists
    result = await db.execute(
        select(ScriptMetadata).where(ScriptMetadata.id == request.script_id)
    )
    script = result.scalar_one_or_none()
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Create report record
    report_id = str(uuid.uuid4())
    report = CoverageReport(
        id=report_id,
        script_id=request.script_id,
        genre=request.genre,
        comps=request.comps or [],
        analysis_depth=request.analysis_depth,
        status=ReportStatus.PROCESSING,
        subscores={},
        model_used="kimi-k2.5"
    )
    
    db.add(report)
    await db.commit()
    
    try:
        # Run analysis synchronously
        report = await run_coverage_analysis(
            script_text=request.script_text,
            report_id=report_id,
            script_id=request.script_id,
            db=db,
            genre=request.genre,
            comps=request.comps,
            analysis_depth=request.analysis_depth
        )
        
        # Return full response
        return await _format_report_response(report, script, db)
        
    except AnalysisError as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/{report_id}", response_model=CoverageReportResponse)
async def get_coverage(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a coverage report by ID.
    
    If status is 'processing', the content fields will be null.
    Once completed, all fields are populated.
    """
    result = await db.execute(
        select(CoverageReport).where(CoverageReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Get script
    script_result = await db.execute(
        select(ScriptMetadata).where(ScriptMetadata.id == report.script_id)
    )
    script = script_result.scalar_one_or_none()
    
    return await _format_report_response(report, script, db)


async def _format_report_response(
    report: CoverageReport,
    script: Optional[ScriptMetadata],
    db: AsyncSession
) -> CoverageReportResponse:
    """Format a CoverageReport for API response.
    
    Args:
        report: CoverageReport object
        script: ScriptMetadata object (can be None)
        db: Database session
        
    Returns:
        Formatted CoverageReportResponse
    """
    # Format evidence quotes
    quotes_data = report.evidence_quotes or []
    evidence_quotes = [
        EvidenceQuote(
            quote=q.get("quote", ""),
            page=q.get("page", 0),
            context=q.get("context")
        )
        for q in quotes_data
    ]
    
    return CoverageReportResponse(
        report_id=report.id,
        script_id=report.script_id,
        script_title=script.title if script else None,
        genre=report.genre,
        comps=report.comps,
        analysis_depth=report.analysis_depth,
        status=report.status.value,
        created_at=report.created_at,
        completed_at=report.completed_at,
        subscores=report.subscores,
        total_score=report.total_score,
        recommendation=report.recommendation.value if report.recommendation else None,
        logline=report.logline,
        synopsis=report.synopsis,
        overall_comments=report.overall_comments,
        strengths=report.strengths or [],
        weaknesses=report.weaknesses or [],
        character_notes=report.character_notes,
        structure_analysis=report.structure_analysis,
        market_positioning=report.market_positioning,
        evidence_quotes=evidence_quotes,
        model_used=report.model_used
    )


@router.get("/")
async def list_coverage_reports(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """List all coverage reports for the current user."""
    # TODO: Filter by actual user_id once auth is implemented
    user_id = "default_user"
    
    # Join with ScriptMetadata to filter by user
    result = await db.execute(
        select(CoverageReport, ScriptMetadata)
        .join(ScriptMetadata, CoverageReport.script_id == ScriptMetadata.id)
        .where(ScriptMetadata.user_id == user_id)
        .order_by(CoverageReport.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    reports = []
    for report, script in result.all():
        reports.append(CoverageListResponse(
            report_id=report.id,
            script_id=report.script_id,
            script_title=script.title,
            status=report.status.value,
            total_score=report.total_score,
            recommendation=report.recommendation.value if report.recommendation else None,
            created_at=report.created_at
        ))
    
    return {"reports": reports, "total": len(reports)}


@router.delete("/{report_id}")
async def delete_coverage(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a coverage report."""
    result = await db.execute(
        select(CoverageReport).where(CoverageReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    await db.delete(report)
    await db.commit()
    
    return {"message": "Coverage report deleted successfully"}


class ExportRequest(BaseModel):
    """Request to export a coverage report."""
    email: Optional[str] = None  # Email to share Google Doc with


class ExportResponse(BaseModel):
    """Response from export operation."""
    export_type: str  # 'google_doc' or 'pdf'
    url: Optional[str] = None  # URL to exported document
    filename: Optional[str] = None  # Filename for PDF download
    message: str


@router.post("/{report_id}/export/google-doc", response_model=ExportResponse)
async def export_to_google_doc(
    report_id: str,
    request: ExportRequest,
    db: AsyncSession = Depends(get_db)
):
    """Export a coverage report to Google Docs.
    
    Creates a formatted Google Doc with the coverage report content
    and optionally shares it with the specified email address.
    
    The document includes:
    - Formatted headers and sections
    - Scores and recommendation badge
    - All coverage components (logline, synopsis, etc.)
    - Evidence quotes
    """
    # Get report
    result = await db.execute(
        select(CoverageReport).where(CoverageReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail="Report is not completed yet"
        )
    
    # Get script info
    script_result = await db.execute(
        select(ScriptMetadata).where(ScriptMetadata.id == report.script_id)
    )
    script = script_result.scalar_one_or_none()
    
    try:
        # Prepare report data
        report_data = {
            'script_title': script.title if script else 'Untitled Script',
            'total_score': report.total_score,
            'recommendation': report.recommendation.value if report.recommendation else 'N/A',
            'subscores': report.subscores,
            'logline': report.logline,
            'synopsis': report.synopsis,
            'overall_comments': report.overall_comments,
            'strengths': report.strengths,
            'weaknesses': report.weaknesses,
            'character_notes': report.character_notes,
            'structure_analysis': report.structure_analysis,
            'market_positioning': report.market_positioning,
            'evidence_quotes': report.evidence_quotes
        }
        
        # Default to Philip's email if not specified
        share_email = request.email or "philipriccio@gmail.com"
        
        # Export to Google Docs
        exporter = get_google_docs_exporter()
        result = exporter.export_coverage_report(
            report_data=report_data,
            share_with=share_email
        )
        
        return ExportResponse(
            export_type='google_doc',
            url=result['url'],
            message=f"Google Doc created successfully and shared with {share_email}"
        )
        
    except GoogleDocsExportError as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/{report_id}/export/pdf")
async def export_to_pdf(
    report_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Export a coverage report to PDF.
    
    Generates a professionally formatted PDF with:
    - Color-coded recommendation badge
    - Score breakdown
    - All coverage sections
    - Evidence quotes with styling
    
    Returns the PDF as a downloadable file.
    """
    # Get report
    result = await db.execute(
        select(CoverageReport).where(CoverageReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail="Report is not completed yet"
        )
    
    # Get script info
    script_result = await db.execute(
        select(ScriptMetadata).where(ScriptMetadata.id == report.script_id)
    )
    script = script_result.scalar_one_or_none()
    
    try:
        # Prepare report data
        report_data = {
            'script_title': script.title if script else 'Untitled Script',
            'total_score': report.total_score,
            'recommendation': report.recommendation.value if report.recommendation else 'N/A',
            'subscores': report.subscores,
            'logline': report.logline,
            'synopsis': report.synopsis,
            'overall_comments': report.overall_comments,
            'strengths': report.strengths,
            'weaknesses': report.weaknesses,
            'character_notes': report.character_notes,
            'structure_analysis': report.structure_analysis,
            'market_positioning': report.market_positioning,
            'evidence_quotes': report.evidence_quotes
        }
        
        # Generate PDF
        exporter = get_pdf_exporter()
        pdf_content = exporter.export_coverage_report(report_data)
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d")
        safe_title = ''.join(c if c.isalnum() else '_' for c in (script.title if script else 'Untitled'))
        filename = f"Coverage_Report_{safe_title}_{timestamp}.pdf"
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except PDFExportError as e:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")