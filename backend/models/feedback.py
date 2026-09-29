"""
FeedbackItem ORM model.

Represents a single piece of raw user feedback from any source
(Reddit, YouTube, Play Store, Community, App Store, CSV upload).

Schema matches architecture §3.1.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Boolean, Float, DateTime, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

from backend.db.database import Base


class SourceType(str, enum.Enum):
    """Supported feedback sources."""
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    COMMUNITY = "community"
    PLAYSTORE = "playstore"
    APPSTORE = "appstore"
    CSV_UPLOAD = "csv_upload"


class ExtractionStatus(str, enum.Enum):
    """Extraction pipeline status for a feedback item."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FeedbackItem(Base):
    """
    Raw user feedback from any source.

    Each row represents one post, comment, review, or uploaded entry.
    Linked to zero or more RetrievalEpisodes via extraction.
    """

    __tablename__ = "feedback_items"

    # ── Primary Key ───────────────────────────────────────────
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique identifier (UUID)"
    )

    # ── Source Information ─────────────────────────────────────
    source = Column(
        SQLEnum(SourceType),
        nullable=False,
        index=True,
        doc="Platform source of this feedback"
    )
    source_url = Column(
        String(2048),
        nullable=True,
        doc="URL to the original post/comment/review"
    )
    author_id = Column(
        String(255),
        nullable=True,
        index=True,
        doc="Anonymized hash of the original author"
    )

    # ── Content ───────────────────────────────────────────────
    text = Column(
        Text,
        nullable=False,
        doc="Original user feedback text"
    )
    date = Column(
        DateTime,
        nullable=True,
        doc="Date the feedback was originally posted"
    )

    # ── Thread Structure ──────────────────────────────────────
    thread_id = Column(
        String(255),
        nullable=True,
        index=True,
        doc="Thread/post ID for grouping related feedback"
    )
    parent_id = Column(
        String(255),
        nullable=True,
        doc="Parent comment/post ID for reply chains"
    )

    # ── Platform-Specific Metadata ────────────────────────────
    platform_metadata = Column(
        JSON,
        nullable=True,
        default=dict,
        doc="Source-specific metadata (subreddit, score, rating, etc.)"
    )

    # ── Relevance Classification ──────────────────────────────
    is_relevant = Column(
        Boolean,
        nullable=True,
        default=None,
        index=True,
        doc="Whether this feedback relates to photo retrieval"
    )
    relevance_score = Column(
        Float,
        nullable=True,
        default=None,
        doc="Confidence score from relevance classifier (0.0-1.0)"
    )

    # ── Deduplication ─────────────────────────────────────────
    fingerprint = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="SHA-256 fingerprint for deduplication"
    )

    # ── Timestamps ────────────────────────────────────────────
    ingested_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="When this item was ingested into the system"
    )

    # ── Extraction Pipeline ───────────────────────────────────
    extraction_status = Column(
        SQLEnum(ExtractionStatus),
        nullable=False,
        default=ExtractionStatus.PENDING,
        index=True,
        doc="Current status in the extraction pipeline"
    )

    # ── Relationships ─────────────────────────────────────────
    episodes = relationship(
        "RetrievalEpisode",
        back_populates="feedback_item",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<FeedbackItem(id={self.id[:8]}..., "
            f"source={self.source.value}, "
            f"relevant={self.is_relevant}, "
            f"status={self.extraction_status.value})>"
        )
