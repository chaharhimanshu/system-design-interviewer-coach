"""
Session API Schemas
Pydantic models for session API requests and responses
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from app.domain.entities.session import (
    SessionStatus,
    DifficultyLevel,
    MessageType,
)

if TYPE_CHECKING:
    from app.domain.entities.session import InterviewSession


class SessionConfigRequest(BaseModel):
    """Request model for session configuration"""

    topic: str = Field(..., min_length=3, max_length=200, description="Interview topic")
    difficulty_level: DifficultyLevel = Field(default=DifficultyLevel.INTERMEDIATE)
    max_duration_minutes: int = Field(
        default=60, ge=15, le=180, description="Max session duration"
    )
    enable_hints: bool = Field(default=True)
    enable_real_time_feedback: bool = Field(default=True)
    custom_requirements: Optional[str] = Field(None, max_length=1000)

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v):
        if not v.strip():
            raise ValueError("Topic cannot be empty")
        return v.strip()


class CreateSessionRequest(BaseModel):
    """Request to create new interview session"""

    config: SessionConfigRequest


class MessageRequest(BaseModel):
    """Request to send a message"""

    content: str = Field(..., min_length=1, max_length=5000)
    message_type: MessageType = Field(default=MessageType.TEXT)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    """Response model for interview sessions"""

    session_id: UUID
    user_id: UUID
    topic: str
    difficulty_level: DifficultyLevel
    status: SessionStatus
    started_at: datetime
    ended_at: Optional[datetime]
    total_duration: Optional[int]  # in seconds
    max_duration_minutes: int
    enable_hints: bool
    enable_real_time_feedback: bool
    custom_requirements: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, session: "InterviewSession") -> "SessionResponse":
        """Create response from domain entity"""
        return cls(
            session_id=session.session_id,
            user_id=session.user_id,
            topic=session.config.topic,
            difficulty_level=session.config.difficulty_level,
            status=session.status,
            started_at=session.started_at,
            ended_at=session.ended_at,
            total_duration=session.total_duration,
            max_duration_minutes=session.config.max_duration_minutes,
            enable_hints=session.config.enable_hints,
            enable_real_time_feedback=session.config.enable_real_time_feedback,
            custom_requirements=session.config.custom_requirements,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=len(session.messages),
        )


class SessionListResponse(BaseModel):
    """Response for session list"""

    sessions: List[SessionResponse]
    total_count: int
    has_more: bool
