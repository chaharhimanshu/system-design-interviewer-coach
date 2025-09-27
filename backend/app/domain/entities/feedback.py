"""
Feedback Domain Entity
Represents user feedback for interview sessions
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from dataclasses import dataclass, field


@dataclass
class Feedback:
    """Domain entity for session feedback"""
    
    feedback_id: UUID = field(default_factory=uuid.uuid4)
    session_id: UUID = field(default=None)
    user_id: UUID = field(default=None)
    overall_rating: int = field(default=1)  # 1-5 scale
    ai_quality_rating: int = field(default=1)  # 1-5 scale
    user_experience_rating: int = field(default=1)  # 1-5 scale
    comments: Optional[str] = field(default=None)
    suggestions: Optional[str] = field(default=None)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate feedback data after initialization"""
        if not (1 <= self.overall_rating <= 5):
            raise ValueError("Overall rating must be between 1 and 5")
        if not (1 <= self.ai_quality_rating <= 5):
            raise ValueError("AI quality rating must be between 1 and 5")
        if not (1 <= self.user_experience_rating <= 5):
            raise ValueError("User experience rating must be between 1 and 5")
        
        if self.comments and len(self.comments) > 2000:
            raise ValueError("Comments cannot exceed 2000 characters")
        if self.suggestions and len(self.suggestions) > 2000:
            raise ValueError("Suggestions cannot exceed 2000 characters")


@dataclass
class Evaluation:
    """Domain entity for session evaluation"""
    
    evaluation_id: UUID = field(default_factory=uuid.uuid4)
    session_id: UUID = field(default=None)
    technical_score: Optional[int] = field(default=None)  # 0-100
    design_score: Optional[int] = field(default=None)  # 0-100
    communication_score: Optional[int] = field(default=None)  # 0-100
    problem_solving_score: Optional[int] = field(default=None)  # 0-100
    overall_grade: Optional[str] = field(default=None)  # A+, A, A-, B+, etc.
    strengths: Optional[str] = field(default=None)
    weaknesses: Optional[str] = field(default=None)
    improvement_areas: Optional[str] = field(default=None)
    detailed_feedback: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate evaluation data after initialization"""
        score_fields = [
            self.technical_score, 
            self.design_score, 
            self.communication_score, 
            self.problem_solving_score
        ]
        
        for score in score_fields:
            if score is not None and not (0 <= score <= 100):
                raise ValueError("All scores must be between 0 and 100")
        
        valid_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
        if self.overall_grade and self.overall_grade not in valid_grades:
            raise ValueError(f"Overall grade must be one of: {', '.join(valid_grades)}")

    def calculate_average_score(self) -> Optional[float]:
        """Calculate average score from individual scores"""
        scores = [
            score for score in [
                self.technical_score, 
                self.design_score, 
                self.communication_score, 
                self.problem_solving_score
            ] if score is not None
        ]
        
        if not scores:
            return None
            
        return sum(scores) / len(scores)


@dataclass
class ConversationSummary:
    """Domain entity for conversation summary"""
    
    summary_id: UUID = field(default_factory=uuid.uuid4)
    session_id: UUID = field(default=None)
    summary_text: Optional[str] = field(default=None)
    key_topics: list = field(default_factory=list)
    user_performance_notes: Optional[str] = field(default=None)
    message_count: int = field(default=0)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate summary data after initialization"""
        if self.message_count < 0:
            raise ValueError("Message count cannot be negative")