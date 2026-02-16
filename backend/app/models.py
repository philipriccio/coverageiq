"""Database models for CoverageIQ.

Privacy-first design: Script content is NEVER stored.
Only metadata and generated reports are persisted.
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ScriptFormat(str, Enum):
    """Supported script formats."""
    PDF = "pdf"
    FDX = "fdx"


class ReportStatus(str, Enum):
    """Status of coverage report generation."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Recommendation(str, Enum):
    """Overall recommendation based on total score."""
    PASS = "Pass"           # 0-24: Not ready for consideration
    CONSIDER = "Consider"   # 25-37: Shows promise with reservations
    RECOMMEND = "Recommend" # 38-50: Strong contender


class ScriptMetadata(Base):
    """Metadata about uploaded scripts. NO script content is stored.
    
    Privacy Note: This table contains only metadata (title, page count, hashes).
    The actual script content is processed in-memory only and never persisted.
    """
    __tablename__ = "script_metadata"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # File metadata (NOT the file itself or its content)
    filename_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 of filename
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA256 of content
    format: Mapped[ScriptFormat] = mapped_column(SQLEnum(ScriptFormat), nullable=False)
    
    # Script metadata extracted during processing
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    reports: Mapped[List["CoverageReport"]] = relationship(
        "CoverageReport", 
        back_populates="script",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ScriptMetadata(id={self.id}, title={self.title}, format={self.format})>"


class CoverageReport(Base):
    """Generated coverage report for a script.
    
    Contains all analysis results including scores, commentary, and evidence quotes.
    NO raw script content is stored here.
    """
    __tablename__ = "coverage_reports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    script_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("script_metadata.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Analysis configuration
    genre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    comps: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # Comparable films
    analysis_depth: Mapped[str] = mapped_column(String(20), default="standard")  # quick/standard/deep
    
    # Status tracking
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus), 
        default=ReportStatus.PROCESSING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Subscores (5 categories × /10 = /50 total)
    subscores: Mapped[dict] = mapped_column(JSON, default=dict)  # {category: score}
    # Example: {"concept": 8, "structure": 7, "character": 9, "market": 6, "writing": 8}
    
    total_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # /50
    recommendation: Mapped[Optional[Recommendation]] = mapped_column(
        SQLEnum(Recommendation), 
        nullable=True
    )
    
    # Report content
    logline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    synopsis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overall_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    strengths: Mapped[List[str]] = mapped_column(JSON, default=list)
    weaknesses: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    character_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structure_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    market_positioning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Evidence quotes (1-2 lines max, with page references)
    evidence_quotes: Mapped[List[dict]] = mapped_column(JSON, default=list)
    # Example: [{"quote": "Dialogue here", "page": 23, "context": "brief note"}]
    
    # LLM metadata
    model_used: Mapped[str] = mapped_column(String(50), default="kimi-k2.5")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Data retention - for automated cleanup (90 days from creation)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=90)
    )
    
    # Relationships
    script: Mapped["ScriptMetadata"] = relationship("ScriptMetadata", back_populates="reports")
    
    def calculate_recommendation(self) -> Optional[Recommendation]:
        """Calculate recommendation based on total score."""
        if self.total_score is None:
            return None
        if self.total_score >= 38:
            return Recommendation.RECOMMEND
        elif self.total_score >= 25:
            return Recommendation.CONSIDER
        else:
            return Recommendation.PASS
    
    def __repr__(self) -> str:
        return f"<CoverageReport(id={self.id}, script_id={self.script_id}, status={self.status})>"
