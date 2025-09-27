"""
SQLAlchemy Feedback Models
Database representation of Feedback, Evaluation, and ConversationSummary entities
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    Text,
    Enum,
    JSON,
    ForeignKey,
    Index,
    DECIMAL,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base
from app.domain.entities.feedback import Feedback, Evaluation, ConversationSummary


class FeedbackModel(Base):
    """SQLAlchemy Feedback model"""

    __tablename__ = "feedback"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Rating fields
    overall_rating = Column(Integer, nullable=False)
    ai_quality_rating = Column(Integer, nullable=False)
    user_experience_rating = Column(Integer, nullable=False)

    # Text fields
    comments = Column(Text)
    suggestions = Column(Text)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc)
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_feedback_session_id", "session_id"),
        Index("idx_feedback_user_id", "user_id"),
        Index("idx_feedback_created_at", "created_at"),
        CheckConstraint('overall_rating >= 1 AND overall_rating <= 5', name='chk_overall_rating'),
        CheckConstraint('ai_quality_rating >= 1 AND ai_quality_rating <= 5', name='chk_ai_quality_rating'),
        CheckConstraint('user_experience_rating >= 1 AND user_experience_rating <= 5', name='chk_user_experience_rating'),
    )

    @classmethod
    def from_entity(cls, feedback: Feedback) -> "FeedbackModel":
        """Convert Feedback entity to FeedbackModel"""
        return cls(
            id=feedback.feedback_id,
            session_id=feedback.session_id,
            user_id=feedback.user_id,
            overall_rating=feedback.overall_rating,
            ai_quality_rating=feedback.ai_quality_rating,
            user_experience_rating=feedback.user_experience_rating,
            comments=feedback.comments,
            suggestions=feedback.suggestions,
            created_at=feedback.created_at,
        )

    def to_entity(self) -> Feedback:
        """Convert FeedbackModel to Feedback entity"""
        return Feedback(
            feedback_id=self.id,
            session_id=self.session_id,
            user_id=self.user_id,
            overall_rating=self.overall_rating,
            ai_quality_rating=self.ai_quality_rating,
            user_experience_rating=self.user_experience_rating,
            comments=self.comments,
            suggestions=self.suggestions,
            created_at=self.created_at,
        )

    def update_from_entity(self, feedback: Feedback) -> None:
        """Update model fields from Feedback entity"""
        self.overall_rating = feedback.overall_rating
        self.ai_quality_rating = feedback.ai_quality_rating
        self.user_experience_rating = feedback.user_experience_rating
        self.comments = feedback.comments
        self.suggestions = feedback.suggestions


class EvaluationModel(Base):
    """SQLAlchemy Evaluation model"""

    __tablename__ = "evaluations"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Score fields
    technical_score = Column(Integer)
    design_score = Column(Integer)
    communication_score = Column(Integer)
    problem_solving_score = Column(Integer)

    # Overall grade
    overall_grade = Column(String(2))

    # Text feedback fields
    strengths = Column(Text)
    weaknesses = Column(Text)
    improvement_areas = Column(Text)

    # Detailed feedback as JSON
    detailed_feedback = Column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc)
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_evaluations_session_id", "session_id"),
        Index("idx_evaluations_created_at", "created_at"),
        CheckConstraint('technical_score >= 0 AND technical_score <= 100', name='chk_technical_score'),
        CheckConstraint('design_score >= 0 AND design_score <= 100', name='chk_design_score'),
        CheckConstraint('communication_score >= 0 AND communication_score <= 100', name='chk_communication_score'),
        CheckConstraint('problem_solving_score >= 0 AND problem_solving_score <= 100', name='chk_problem_solving_score'),
        CheckConstraint("overall_grade IN ('A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F')", name='chk_overall_grade'),
    )

    @classmethod
    def from_entity(cls, evaluation: Evaluation) -> "EvaluationModel":
        """Convert Evaluation entity to EvaluationModel"""
        return cls(
            id=evaluation.evaluation_id,
            session_id=evaluation.session_id,
            technical_score=evaluation.technical_score,
            design_score=evaluation.design_score,
            communication_score=evaluation.communication_score,
            problem_solving_score=evaluation.problem_solving_score,
            overall_grade=evaluation.overall_grade,
            strengths=evaluation.strengths,
            weaknesses=evaluation.weaknesses,
            improvement_areas=evaluation.improvement_areas,
            detailed_feedback=evaluation.detailed_feedback,
            created_at=evaluation.created_at,
        )

    def to_entity(self) -> Evaluation:
        """Convert EvaluationModel to Evaluation entity"""
        return Evaluation(
            evaluation_id=self.id,
            session_id=self.session_id,
            technical_score=self.technical_score,
            design_score=self.design_score,
            communication_score=self.communication_score,
            problem_solving_score=self.problem_solving_score,
            overall_grade=self.overall_grade,
            strengths=self.strengths,
            weaknesses=self.weaknesses,
            improvement_areas=self.improvement_areas,
            detailed_feedback=self.detailed_feedback,
            created_at=self.created_at,
        )

    def update_from_entity(self, evaluation: Evaluation) -> None:
        """Update model fields from Evaluation entity"""
        self.technical_score = evaluation.technical_score
        self.design_score = evaluation.design_score
        self.communication_score = evaluation.communication_score
        self.problem_solving_score = evaluation.problem_solving_score
        self.overall_grade = evaluation.overall_grade
        self.strengths = evaluation.strengths
        self.weaknesses = evaluation.weaknesses
        self.improvement_areas = evaluation.improvement_areas
        self.detailed_feedback = evaluation.detailed_feedback


class ConversationSummaryModel(Base):
    """SQLAlchemy ConversationSummary model"""

    __tablename__ = "conversation_summaries"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Summary fields
    summary_text = Column(Text)
    key_topics = Column(JSON, nullable=False, default=list)
    user_performance_notes = Column(Text)
    message_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc)
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_conversation_summaries_session_id", "session_id"),
        Index("idx_conversation_summaries_created_at", "created_at"),
        CheckConstraint('message_count >= 0', name='chk_message_count'),
    )

    @classmethod
    def from_entity(cls, summary: ConversationSummary) -> "ConversationSummaryModel":
        """Convert ConversationSummary entity to ConversationSummaryModel"""
        return cls(
            id=summary.summary_id,
            session_id=summary.session_id,
            summary_text=summary.summary_text,
            key_topics=summary.key_topics,
            user_performance_notes=summary.user_performance_notes,
            message_count=summary.message_count,
            created_at=summary.created_at,
        )

    def to_entity(self) -> ConversationSummary:
        """Convert ConversationSummaryModel to ConversationSummary entity"""
        return ConversationSummary(
            summary_id=self.id,
            session_id=self.session_id,
            summary_text=self.summary_text,
            key_topics=self.key_topics or [],
            user_performance_notes=self.user_performance_notes,
            message_count=self.message_count,
            created_at=self.created_at,
        )

    def update_from_entity(self, summary: ConversationSummary) -> None:
        """Update model fields from ConversationSummary entity"""
        self.summary_text = summary.summary_text
        self.key_topics = summary.key_topics
        self.user_performance_notes = summary.user_performance_notes
        self.message_count = summary.message_count