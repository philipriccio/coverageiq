"""Coverage report generation endpoints."""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AnalysisJob, CoverageExample, CoverageReport, DomainKnowledge, JobStatus, Recommendation, ReportStatus, ScriptMetadata
from app.services.analysis import AnalysisError, run_coverage_analysis
from app.services.google_docs_export import GoogleDocsExportError, get_google_docs_exporter
from app.services.job_manager import JobManager
from app.services.pdf_export import PDFExportError, get_pdf_exporter

router = APIRouter(prefix="/api/coverage", tags=["coverage"])


class AsyncCoverageRequest(BaseModel):
    script_id: str
    script_text: str
    genre: Optional[str] = None
    comps: Optional[List[str]] = None
    analysis_depth: str = "standard"


class AsyncJobResponse(BaseModel):
    job_id: str
    report_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    report_id: Optional[str]
    status: str
    progress: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class EvidenceQuote(BaseModel):
    quote: str
    page: int
    context: Optional[str] = None


class CoverageReportResponse(BaseModel):
    report_id: str
    script_id: str
    script_title: Optional[str]
    genre: Optional[str]
    comps: Optional[List[str]]
    analysis_depth: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    subscores: Optional[dict]
    mandate_checklist: Optional[dict]
    total_score: Optional[int]
    recommendation: Optional[str]
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
    is_flagged_example: bool = False


class CoverageHistoryItem(BaseModel):
    id: str
    title: Optional[str]
    genre: Optional[str]
    analysis_depth: str
    recommendation: Optional[str]
    total_score: Optional[int]
    created_at: datetime
    model_used: str


class DomainKnowledgeRequest(BaseModel):
    category: str
    content: str


class DomainKnowledgePatchRequest(BaseModel):
    category: Optional[str] = None
    content: Optional[str] = None


class ExportRequest(BaseModel):
    email: Optional[str] = None


class ExportResponse(BaseModel):
    export_type: str
    url: Optional[str] = None
    filename: Optional[str] = None
    message: str


@router.post("/generate-async", response_model=AsyncJobResponse)
async def generate_coverage_async(request: AsyncCoverageRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScriptMetadata).where(ScriptMetadata.id == request.script_id))
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    report_id = str(uuid.uuid4())
    report = CoverageReport(
        id=report_id,
        script_id=request.script_id,
        genre=request.genre,
        comps=request.comps or [],
        analysis_depth=request.analysis_depth,
        status=ReportStatus.PROCESSING,
        subscores={},
        model_used="gpt-4.1",
    )
    db.add(report)
    await db.commit()

    job = await JobManager.create_job(
        script_id=request.script_id,
        script_text=request.script_text,
        report_id=report_id,
        db=db,
        genre=request.genre,
        comps=request.comps,
        analysis_depth=request.analysis_depth,
    )
    JobManager.start_background_task(job_id=job.id, script_text=request.script_text, report_id=report_id)
    return AsyncJobResponse(job_id=job.id, report_id=report_id, status=JobStatus.QUEUED.value, message="Analysis started")


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await JobManager.get_job(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job.id,
        report_id=job.report_id,
        status=job.status.value,
        progress=job.progress,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
    )


async def _format_report_response(report: CoverageReport, script: Optional[ScriptMetadata], db: AsyncSession) -> CoverageReportResponse:
    quotes = [EvidenceQuote(quote=q.get("quote", ""), page=q.get("page", 0), context=q.get("context")) for q in (report.evidence_quotes or [])]
    example_result = await db.execute(select(CoverageExample).where(CoverageExample.coverage_report_id == report.id))
    example = example_result.scalar_one_or_none()
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
        mandate_checklist=report.mandate_checklist,
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
        evidence_quotes=quotes,
        model_used=report.model_used,
        is_flagged_example=example is not None and example.is_featured,
    )


@router.get("/history")
async def get_coverage_history(db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 20):
    result = await db.execute(
        select(CoverageReport, ScriptMetadata)
        .join(ScriptMetadata, CoverageReport.script_id == ScriptMetadata.id)
        .where(ScriptMetadata.user_id == "default_user")
        .order_by(CoverageReport.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()
    count_result = await db.execute(
        select(func.count(CoverageReport.id))
        .join(ScriptMetadata, CoverageReport.script_id == ScriptMetadata.id)
        .where(ScriptMetadata.user_id == "default_user")
    )
    total = count_result.scalar() or 0
    items = [
        CoverageHistoryItem(
            id=report.id,
            title=script.title,
            genre=report.genre,
            analysis_depth=report.analysis_depth,
            recommendation=report.recommendation.value if report.recommendation else None,
            total_score=report.total_score,
            created_at=report.created_at,
            model_used=report.model_used,
        ).model_dump()
        for report, script in rows
    ]
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/{report_id}", response_model=CoverageReportResponse)
async def get_coverage(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CoverageReport).where(CoverageReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    script_result = await db.execute(select(ScriptMetadata).where(ScriptMetadata.id == report.script_id))
    script = script_result.scalar_one_or_none()
    return await _format_report_response(report, script, db)


@router.post("/{report_id}/flag-example")
async def flag_report_as_example(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CoverageReport).where(CoverageReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Only completed reports can be starred")

    script_result = await db.execute(select(ScriptMetadata).where(ScriptMetadata.id == report.script_id))
    script = script_result.scalar_one_or_none()
    example_result = await db.execute(select(CoverageExample).where(CoverageExample.coverage_report_id == report.id))
    example = example_result.scalar_one_or_none()
    if example:
        example.is_featured = True
    else:
        example = CoverageExample(
            id=str(uuid.uuid4()),
            script_title=script.title if script and script.title else "Untitled Script",
            genre=report.genre,
            analysis_depth=report.analysis_depth,
            coverage_report_id=report.id,
            is_featured=True,
        )
        db.add(example)
    await db.commit()
    return {"message": "Report flagged as example", "example_id": example.id}


@router.get("/admin/knowledge")
async def list_domain_knowledge(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DomainKnowledge).order_by(DomainKnowledge.category.asc(), DomainKnowledge.updated_at.desc()))
    entries = result.scalars().all()
    return {
        "entries": [
            {
                "id": entry.id,
                "category": entry.category,
                "content": entry.content,
                "created_at": entry.created_at,
                "updated_at": entry.updated_at,
            }
            for entry in entries
        ]
    }


@router.post("/admin/knowledge")
async def create_domain_knowledge(request: DomainKnowledgeRequest, db: AsyncSession = Depends(get_db)):
    entry = DomainKnowledge(id=str(uuid.uuid4()), category=request.category.strip().lower(), content=request.content.strip())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {"id": entry.id, "message": "Knowledge entry created"}


@router.patch("/admin/knowledge/{entry_id}")
async def update_domain_knowledge(entry_id: str, request: DomainKnowledgePatchRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DomainKnowledge).where(DomainKnowledge.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    if request.category is not None:
        entry.category = request.category.strip().lower()
    if request.content is not None:
        entry.content = request.content.strip()
    entry.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(entry)
    return {
        "id": entry.id,
        "category": entry.category,
        "content": entry.content,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }


@router.delete("/admin/knowledge/{entry_id}")
async def delete_domain_knowledge(entry_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DomainKnowledge).where(DomainKnowledge.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    await db.delete(entry)
    await db.commit()
    return {"message": "Knowledge entry deleted"}


@router.post("/{report_id}/export/google-doc", response_model=ExportResponse)
async def export_to_google_doc(report_id: str, request: ExportRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CoverageReport).where(CoverageReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report is not completed yet")
    script_result = await db.execute(select(ScriptMetadata).where(ScriptMetadata.id == report.script_id))
    script = script_result.scalar_one_or_none()
    report_data = {
        "script_title": script.title if script else "Untitled Script",
        "total_score": report.total_score,
        "recommendation": report.recommendation.value if report.recommendation else "N/A",
        "subscores": report.subscores,
        "mandate_checklist": report.mandate_checklist,
        "logline": report.logline,
        "synopsis": report.synopsis,
        "overall_comments": report.overall_comments,
        "strengths": report.strengths,
        "weaknesses": report.weaknesses,
        "character_notes": report.character_notes,
        "structure_analysis": report.structure_analysis,
        "market_positioning": report.market_positioning,
        "evidence_quotes": report.evidence_quotes,
    }
    try:
        result = get_google_docs_exporter().export_coverage_report(report_data=report_data, share_with=request.email or "philipriccio@gmail.com")
        return ExportResponse(export_type="google_doc", url=result["url"], message="Google Doc created successfully")
    except GoogleDocsExportError as exc:
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}") from exc


@router.post("/{report_id}/export/pdf")
async def export_to_pdf(report_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CoverageReport).where(CoverageReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report is not completed yet")
    script_result = await db.execute(select(ScriptMetadata).where(ScriptMetadata.id == report.script_id))
    script = script_result.scalar_one_or_none()
    report_data = {
        "script_title": script.title if script else "Untitled Script",
        "total_score": report.total_score,
        "recommendation": report.recommendation.value if report.recommendation else "N/A",
        "subscores": report.subscores,
        "mandate_checklist": report.mandate_checklist,
        "logline": report.logline,
        "synopsis": report.synopsis,
        "overall_comments": report.overall_comments,
        "strengths": report.strengths,
        "weaknesses": report.weaknesses,
        "character_notes": report.character_notes,
        "structure_analysis": report.structure_analysis,
        "market_positioning": report.market_positioning,
        "evidence_quotes": report.evidence_quotes,
    }
    try:
        pdf_content = get_pdf_exporter().export_coverage_report(report_data)
        timestamp = datetime.now().strftime("%Y%m%d")
        safe_title = "".join(c if c.isalnum() else "_" for c in (script.title if script else "Untitled"))
        filename = f"Coverage_Report_{safe_title}_{timestamp}.pdf"
        return Response(content=pdf_content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})
    except PDFExportError as exc:
        raise HTTPException(status_code=500, detail=f"PDF export failed: {exc}") from exc


@router.post("/generate-sync", response_model=CoverageReportResponse)
async def generate_coverage_sync(request: AsyncCoverageRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScriptMetadata).where(ScriptMetadata.id == request.script_id))
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    report_id = str(uuid.uuid4())
    report = CoverageReport(
        id=report_id,
        script_id=request.script_id,
        genre=request.genre,
        comps=request.comps or [],
        analysis_depth=request.analysis_depth,
        status=ReportStatus.PROCESSING,
        subscores={},
        model_used="gpt-4.1",
    )
    db.add(report)
    await db.commit()
    try:
        updated = await run_coverage_analysis(
            script_text=request.script_text,
            report_id=report_id,
            script_id=request.script_id,
            db=db,
            genre=request.genre,
            comps=request.comps,
            analysis_depth=request.analysis_depth,
        )
        return await _format_report_response(updated, script, db)
    except AnalysisError as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
