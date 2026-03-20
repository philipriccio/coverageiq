"""Database models for CoverageIQ.

Privacy-first design: Script content is NEVER stored.
Only metadata, generated reports, curated examples, and domain knowledge are persisted.
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List

from sqlalchemy import String, Integer, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ScriptFormat(str, Enum):
    PDF = "pdf"
    FDX = "fdx"


class ReportStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Recommendation(str, Enum):
    PASS = "Pass"
    CONSIDER = "Consider"
    RECOMMEND = "Recommend"


class ScriptMetadata(Base):
    __tablename__ = "script_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    filename_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    format: Mapped[ScriptFormat] = mapped_column(SQLEnum(ScriptFormat), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    script_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    reports: Mapped[List["CoverageReport"]] = relationship(
        "CoverageReport",
        back_populates="script",
        cascade="all, delete-orphan",
    )


class CoverageReport(Base):
    __tablename__ = "coverage_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    script_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("script_metadata.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    genre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    comps: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    analysis_depth: Mapped[str] = mapped_column(String(20), default="standard")

    status: Mapped[ReportStatus] = mapped_column(SQLEnum(ReportStatus), default=ReportStatus.PROCESSING)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    subscores: Mapped[dict] = mapped_column(JSON, default=dict)
    total_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recommendation: Mapped[Optional[Recommendation]] = mapped_column(SQLEnum(Recommendation), nullable=True)

    logline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    synopsis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overall_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strengths: Mapped[List[str]] = mapped_column(JSON, default=list)
    weaknesses: Mapped[List[str]] = mapped_column(JSON, default=list)
    character_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structure_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    market_positioning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_quotes: Mapped[List[dict]] = mapped_column(JSON, default=list)
    mandate_checklist: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    model_used: Mapped[str] = mapped_column(String(50), default="gpt-4.1")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=90))

    script: Mapped["ScriptMetadata"] = relationship("ScriptMetadata", back_populates="reports")
    examples: Mapped[List["CoverageExample"]] = relationship(
        "CoverageExample",
        back_populates="coverage_report",
        cascade="all, delete-orphan",
    )

    def calculate_recommendation(self) -> Optional[Recommendation]:
        if self.total_score is None:
            return None
        if self.total_score >= 38:
            return Recommendation.RECOMMEND
        if self.total_score >= 25:
            return Recommendation.CONSIDER
        return Recommendation.PASS


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    script_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("script_metadata.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("coverage_reports.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[JobStatus] = mapped_column(SQLEnum(JobStatus), default=JobStatus.QUEUED)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    genre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    comps: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    analysis_depth: Mapped[str] = mapped_column(String(20), default="standard")
    script_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class CoverageExample(Base):
    __tablename__ = "coverage_examples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    script_title: Mapped[str] = mapped_column(String(500), nullable=False)
    genre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    analysis_depth: Mapped[str] = mapped_column(String(20), default="standard")
    coverage_report_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("coverage_reports.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    coverage_report: Mapped["CoverageReport"] = relationship("CoverageReport", back_populates="examples")


class DomainKnowledge(Base):
    __tablename__ = "domain_knowledge"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
