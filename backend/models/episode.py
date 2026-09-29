"""
RetrievalEpisode ORM model.

Represents a structured extraction from a FeedbackItem — capturing
what the user was trying to find, what they remembered, what they
forgot, how they tried to retrieve it, and why it failed.

Schema matches architecture §3.2.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, DateTime, JSON, ForeignKey
)
from sqlalchemy.orm import relationship

from backend.db.database import Base


class RetrievalEpisode(Base):
    """
    Structured retrieval episode extracted from raw feedback.

    Each episode represents one user's attempt to find a photo/video/screenshot.
    Linked to the source FeedbackItem via foreign key.
    """

    __tablename__ = "retrieval_episodes"

    # ── Primary Key ───────────────────────────────────────────
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique identifier (UUID)"
    )

    # ── Foreign Key ───────────────────────────────────────────
    feedback_item_id = Column(
        String(36),
        ForeignKey("feedback_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to the source FeedbackItem"
    )

    # ── Retrieval Context ─────────────────────────────────────
    user_goal = Column(
        Text,
        nullable=True,
        doc="What the user was trying to find (e.g., 'photos from Goa trip 2023')"
    )
    memory_type = Column(
        String(50),
        nullable=True,
        index=True,
        doc="Type of media being sought: photo, screenshot, document, video, etc."
    )

    # ── Structured Extraction Fields ──────────────────────────
    remembered_clues = Column(
        JSON,
        nullable=True,
        default=list,
        doc="What the user remembers: [{type, value}, ...] using controlled vocabulary"
    )
    forgotten_info = Column(
        JSON,
        nullable=True,
        default=list,
        doc="What the user forgot/doesn't know: [{type, value}, ...] using controlled vocabulary"
    )
    retrieval_attempt = Column(
        JSON,
        nullable=True,
        default=list,
        doc="Methods the user tried: [{method, detail}, ...] using controlled vocabulary"
    )
    failure_reason = Column(
        JSON,
        nullable=True,
        default=list,
        doc="Why retrieval failed: list of failure reason enum values"
    )

    # ── Evidence & Outcome ────────────────────────────────────
    desired_outcome = Column(
        Text,
        nullable=True,
        doc="What the user ultimately wanted to achieve"
    )
    supporting_evidence = Column(
        Text,
        nullable=True,
        doc="Verbatim quote from the original feedback text"
    )

    # ── Source Attribution ─────────────────────────────────────
    source = Column(
        String(50),
        nullable=True,
        index=True,
        doc="Source platform (denormalized from FeedbackItem for quick access)"
    )
    source_url = Column(
        String(2048),
        nullable=True,
        doc="URL to the original post (denormalized from FeedbackItem)"
    )

    # ── Clustering ────────────────────────────────────────────
    problem_cluster = Column(
        String(255),
        nullable=True,
        index=True,
        doc="Assigned problem cluster ID after clustering"
    )

    # ── Timestamps ────────────────────────────────────────────
    extracted_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="When this episode was extracted by the LLM"
    )

    # ── Relationships ─────────────────────────────────────────
    feedback_item = relationship(
        "FeedbackItem",
        back_populates="episodes",
    )

    def __repr__(self) -> str:
        goal_preview = (self.user_goal or "")[:50]
        return (
            f"<RetrievalEpisode(id={self.id[:8]}..., "
            f"memory_type={self.memory_type}, "
            f"goal='{goal_preview}...')>"
        )
