"""Script upload and management endpoints."""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ScriptMetadata, ScriptFormat, CoverageReport
from app.services.extractor import ScriptExtractor, PDFExtractionError

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


class ScriptUploadResponse(BaseModel):
    """Response model for successful script upload."""
    script_id: str
    title: Optional[str]
    page_count: int
    format: str
    message: str


class ScriptDetailResponse(BaseModel):
    """Response model for script metadata retrieval."""
    script_id: str
    title: Optional[str]
    author: Optional[str]
    page_count: Optional[int]
    format: str
    created_at: datetime
    report_count: int


@router.post("/upload", response_model=ScriptUploadResponse)
async def upload_script(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload a script file (PDF or FDX) for analysis.
    
    **Privacy Note:** The script file is processed entirely in memory.
    Only metadata (title, page count, file hash) is stored.
    The actual script content is never written to disk or database.
    
    ## Supported Formats
    - **PDF** - Standard PDF files (primary format)
    - **FDX** - Final Draft XML format
    
    ## Process
    1. File is validated and loaded into memory
    2. Text is extracted using pdfplumber (PDF) or lxml (FDX)
    3. Metadata (title, page count, hashes) is extracted
    4. Metadata is stored in database
    5. Script content is discarded from memory
    
    Returns:
        Script metadata including ID for use with analysis endpoints
    """
    # Validate file extension
    filename = file.filename or "unknown"
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if ext not in ['pdf', 'fdx']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: .{ext}. Please upload .pdf or .fdx files only."
        )
    
    # Read file content into memory
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read file: {str(e)}"
        )
    finally:
        await file.close()
    
    # Validate file size (10MB limit)
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    
    if len(content) > ScriptExtractor.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(content) / 1024 / 1024:.1f}MB (max 10MB)"
        )
    
    # Extract text and metadata (memory-only processing)
    try:
        extraction_result = ScriptExtractor.extract(content, filename)
    except PDFExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )
    
    # Create script metadata record (NO script content stored)
    script_id = str(uuid.uuid4())
    
    # Map format string to enum
    format_enum = ScriptFormat.PDF if extraction_result["format"] == "pdf" else ScriptFormat.FDX
    
    script_metadata = ScriptMetadata(
        id=script_id,
        user_id="default_user",  # TODO: Replace with actual auth user ID
        filename_hash=extraction_result["filename_hash"],
        file_hash=extraction_result["file_hash"],
        format=format_enum,
        title=extraction_result.get("title"),
        page_count=extraction_result.get("page_count"),
        created_at=datetime.utcnow()
    )
    
    db.add(script_metadata)
    await db.commit()
    
    # IMPORTANT: extraction_result["text"] is NOT stored
    # It exists only in this function's scope and will be garbage collected
    # The text would be passed to the analysis service here
    
    return ScriptUploadResponse(
        script_id=script_id,
        title=extraction_result.get("title"),
        page_count=extraction_result.get("page_count", 0),
        format=extraction_result["format"],
        message="Script uploaded successfully. Use this ID to start coverage analysis."
    )


@router.get("/list")
async def list_scripts(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """List all uploaded scripts for the current user.
    
    Returns metadata only - no script content is ever returned.
    """
    # TODO: Filter by actual user_id once auth is implemented
    user_id = "default_user"
    
    from sqlalchemy import func
    
    # Get scripts with report count using subquery
    report_count_sq = (
        select(func.count())
        .where(CoverageReport.script_id == ScriptMetadata.id)
        .correlate(ScriptMetadata)
        .scalar_subquery()
    )
    
    result = await db.execute(
        select(ScriptMetadata, report_count_sq.label("report_count"))
        .where(ScriptMetadata.user_id == user_id)
        .order_by(ScriptMetadata.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    scripts = result.all()
    
    return {
        "scripts": [
            {
                "script_id": s.id,
                "title": s.title,
                "page_count": s.page_count,
                "format": s.format.value,
                "created_at": s.created_at.isoformat(),
                "report_count": report_count
            }
            for s, report_count in scripts
        ],
        "total": len(scripts)
    }


@router.get("/{script_id}", response_model=ScriptDetailResponse)
async def get_script(
    script_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get metadata for a specific script.
    
    Returns metadata only - no script content is ever returned.
    """
    result = await db.execute(
        select(ScriptMetadata).where(ScriptMetadata.id == script_id)
    )
    script = result.scalar_one_or_none()
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Count reports using a query to avoid lazy loading issues
    from sqlalchemy import func
    report_count_result = await db.execute(
        select(func.count()).where(CoverageReport.script_id == script.id)
    )
    report_count = report_count_result.scalar()
    
    return ScriptDetailResponse(
        script_id=script.id,
        title=script.title,
        author=script.author,
        page_count=script.page_count,
        format=script.format.value,
        created_at=script.created_at,
        report_count=report_count
    )


@router.delete("/{script_id}")
async def delete_script(
    script_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a script and all its associated reports.
    
    This performs a hard delete - all data is permanently removed.
    """
    result = await db.execute(
        select(ScriptMetadata).where(ScriptMetadata.id == script_id)
    )
    script = result.scalar_one_or_none()
    
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    await db.delete(script)
    await db.commit()
    
    return {"message": "Script and all associated reports deleted successfully"}
