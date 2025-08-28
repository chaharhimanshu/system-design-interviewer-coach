"""
Interview Session Domain Entities
Core business logic for system design interview sessions
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid
from dataclasses import dataclass


class SessionStatus(str, Enum):
    """Interview session status"""

    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class DifficultyLevel(str, Enum):
    """Interview difficulty levels"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class MessageRole(str, Enum):
    """Chat message roles"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Types of messages in the session"""

    TEXT = "text"
    QUESTION = "question"
    ANSWER = "answer"
    FEEDBACK = "feedback"
    CLARIFICATION = "clarification"
    HINT = "hint"


@dataclass
class SessionConfig:
    """Session configuration settings"""

    topic: str
    difficulty_level: DifficultyLevel
    max_duration_minutes: int = 60
    enable_hints: bool = True
    enable_real_time_feedback: bool = True
    custom_requirements: Optional[str] = None


@dataclass
class Message:
    """Chat message in an interview session"""

    message_id: uuid.UUID
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    tokens_used: int = 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}


class InterviewSession:
    """
    Interview Session Domain Entity
    Manages the state and flow of a system design interview
    """

    def __init__(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        config: SessionConfig,
        status: SessionStatus = SessionStatus.ACTIVE,
        started_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
        total_duration: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.config = config
        self.status = status
        self.started_at = started_at or datetime.now(timezone.utc)
        self.ended_at = ended_at
        self.total_duration = total_duration
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.feedback = {}  # Session feedback storage

        # In-memory message history (will be persisted separately)
        self.messages: List[Message] = []

    def add_message(
        self,
        role: MessageRole,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None,
        tokens_used: int = 0,
    ) -> Message:
        """Add a new message to the session"""
        message = Message(
            message_id=uuid.uuid4(),
            role=role,
            content=content,
            message_type=message_type,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
            tokens_used=tokens_used,
        )

        self.messages.append(message)
        self._mark_as_updated()

        return message

    def get_conversation_history(self, limit: Optional[int] = None) -> List[Message]:
        """Get conversation history, optionally limited"""
        messages = sorted(self.messages, key=lambda m: m.timestamp)
        return messages[-limit:] if limit else messages

    def complete_session(self, reason: Optional[str] = None) -> None:
        """Mark session as completed"""
        if self.status == SessionStatus.ACTIVE:
            self.status = SessionStatus.COMPLETED
            self.ended_at = datetime.now(timezone.utc)
            self.total_duration = self._calculate_duration()
            self._mark_as_updated()

    def abandon_session(self, reason: Optional[str] = None) -> None:
        """Mark session as abandoned"""
        if self.status == SessionStatus.ACTIVE:
            self.status = SessionStatus.ABANDONED
            self.ended_at = datetime.now(timezone.utc)
            self.total_duration = self._calculate_duration()
            self._mark_as_updated()

    def extend_session(self, additional_minutes: int) -> None:
        """Extend session duration"""
        if self.status == SessionStatus.ACTIVE:
            self.config.max_duration_minutes += additional_minutes
            self._mark_as_updated()

    def is_expired(self) -> bool:
        """Check if session has exceeded max duration"""
        if self.status != SessionStatus.ACTIVE:
            return False

        duration = self._calculate_duration()
        return duration >= self.config.max_duration_minutes * 60  # Convert to seconds

    def get_session_metrics(self) -> Dict[str, Any]:
        """Get session metrics for analysis"""
        total_messages = len(self.messages)
        user_messages = len([m for m in self.messages if m.role == MessageRole.USER])
        assistant_messages = len(
            [m for m in self.messages if m.role == MessageRole.ASSISTANT]
        )
        total_tokens = sum(m.tokens_used for m in self.messages)

        return {
            "session_id": str(self.session_id),
            "status": self.status.value,
            "topic": self.config.topic,
            "difficulty": self.config.difficulty_level.value,
            "duration_seconds": self._calculate_duration(),
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "total_tokens_used": total_tokens,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }

    def _calculate_duration(self) -> int:
        """Calculate session duration in seconds"""
        if not self.started_at:
            return 0

        end_time = self.ended_at or datetime.now(timezone.utc)
        delta = end_time - self.started_at
        return int(delta.total_seconds())

    def _mark_as_updated(self) -> None:
        """Mark entity as updated"""
        self.updated_at = datetime.now(timezone.utc)

    def __eq__(self, other) -> bool:
        if not isinstance(other, InterviewSession):
            return False
        return self.session_id == other.session_id

    def __hash__(self) -> int:
        return hash(self.session_id)

    def __repr__(self) -> str:
        return f"InterviewSession(session_id={self.session_id}, topic={self.config.topic}, status={self.status})"
