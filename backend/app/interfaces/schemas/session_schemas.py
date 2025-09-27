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
    MessageRole,
)

if TYPE_CHECKING:
    from app.domain.entities.session import InterviewSession, Message


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


class MessageResponse(BaseModel):
    """Response model for chat messages"""
    
    message_id: UUID
    session_id: UUID
    role: MessageRole
    message_type: MessageType
    content: str
    tokens_used: int
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, message: "Message") -> "MessageResponse":
        """Create response from domain entity"""
        return cls(
            message_id=message.message_id,
            session_id=message.session_id,
            role=message.role,
            message_type=message.message_type,
            content=message.content,
            tokens_used=message.tokens_used,
            timestamp=message.timestamp,
            metadata=message.metadata,
        )


class FeedbackResponse(BaseModel):
    """Response model for session feedback"""
    
    feedback_id: UUID
    session_id: UUID
    user_id: UUID
    overall_rating: int = Field(..., ge=1, le=5)
    ai_quality_rating: int = Field(..., ge=1, le=5)
    user_experience_rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None
    suggestions: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DetailedSessionResponse(BaseModel):
    """Detailed response model for interview sessions with full chat history and feedback"""

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
    messages: List[MessageResponse] = Field(default_factory=list)
    feedback: Optional[FeedbackResponse] = None
    message_count: int = 0

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, session: "InterviewSession", feedback=None) -> "DetailedSessionResponse":
        """Create detailed response from domain entity"""
        messages = [MessageResponse.from_entity(msg) for msg in session.messages]
        
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
            messages=messages,
            feedback=feedback,
            message_count=len(messages),
        )


class CreateSessionWithStartRequest(BaseModel):
    """Request to create and start new interview session"""

    config: SessionConfigRequest


class StartSessionResponse(BaseModel):
    """Response for starting a session with opening question"""
    
    session_id: UUID
    user_id: UUID
    topic: str
    difficulty_level: DifficultyLevel
    status: SessionStatus
    started_at: datetime
    max_duration_minutes: int
    opening_question: str
    message_id: UUID
    expected_topics: List[str] = Field(default_factory=list)
    context: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_session_and_message(
        cls, 
        session: "InterviewSession", 
        opening_message: "Message",
        ai_response: Dict[str, Any]
    ) -> "StartSessionResponse":
        """Create response from session, opening message, and AI response"""
        return cls(
            session_id=session.session_id,
            user_id=session.user_id,
            topic=session.config.topic,
            difficulty_level=session.config.difficulty_level,
            status=session.status,
            started_at=session.started_at,
            max_duration_minutes=session.config.max_duration_minutes,
            opening_question=opening_message.content,
            message_id=opening_message.message_id,
            expected_topics=ai_response.get("expected_topics", []),
            context=ai_response.get("context", ""),
        )


class SessionListResponse(BaseModel):
    """Response for session list"""

    sessions: List[SessionResponse]
    total_count: int
    has_more: bool
