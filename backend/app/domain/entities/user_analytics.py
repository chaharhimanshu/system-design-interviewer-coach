"""
User Analytics Domain Entity
Separate entity for tracking user performance and interview statistics
"""

from datetime import datetime, timezone, date
from typing import Optional
from dataclasses import dataclass
import uuid


@dataclass
class UserAnalytics:
    """User analytics and performance tracking"""
    
    id: Optional[uuid.UUID] = None
    user_id: uuid.UUID = None
    avg_score: Optional[float] = None
    streak: int = 0
    best_streak: int = 0  # Track the best streak achieved
    total_interviews: int = 0  # Total interviews ever completed
    interviews_left: int = 0
    interviews_this_month: int = 0
    interviews_today: int = 0
    last_interview_date: Optional[date] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.id is None:
            self.id = uuid.uuid4()
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)

    def can_start_interview(self, max_interviews_per_month: int) -> bool:
        """Check if user can start a new interview based on monthly limits"""
        return self.interviews_this_month < max_interviews_per_month

    def get_remaining_interviews(self, max_interviews_per_month: int) -> int:
        """Get remaining interviews for current month"""
        return max(0, max_interviews_per_month - self.interviews_this_month)

    def record_interview(self) -> None:
        """Record a new interview session"""
        now = datetime.now(timezone.utc)
        
        # Reset daily counter if it's a new day
        if (
            self.last_interview_date
            and self.last_interview_date != now.date()
        ):
            self.interviews_today = 0

        # Reset monthly counter if it's a new month
        if self.last_interview_date and (
            self.last_interview_date.month != now.month
            or self.last_interview_date.year != now.year
        ):
            self.interviews_this_month = 0

        # Increment counters
        self.interviews_this_month += 1
        self.interviews_today += 1
        self.total_interviews += 1  # Track total interviews
        self.last_interview_date = now.date()
        self.updated_at = now

    def update_score(self, new_score: float) -> None:
        """Update average score with new score"""
        if self.avg_score is None:
            self.avg_score = new_score
        else:
            # Simple moving average - in production, you might want a more sophisticated approach
            self.avg_score = (self.avg_score + new_score) / 2
        
        self.updated_at = datetime.now(timezone.utc)

    def increment_streak(self) -> None:
        """Increment the user's streak"""
        self.streak += 1
        # Update best streak if current streak is better
        if self.streak > self.best_streak:
            self.best_streak = self.streak
        self.updated_at = datetime.now(timezone.utc)

    def reset_streak(self) -> None:
        """Reset the user's streak"""
        self.streak = 0
        self.updated_at = datetime.now(timezone.utc)

    def reset_monthly_counters(self) -> None:
        """Reset monthly interview counters"""
        self.interviews_this_month = 0
        self.updated_at = datetime.now(timezone.utc)

    @property
    def average_score(self) -> Optional[float]:
        """Alias for avg_score for API compatibility"""
        return self.avg_score
    
    @property
    def current_streak(self) -> int:
        """Alias for streak for API compatibility"""
        return self.streak

    def _mark_as_updated(self) -> None:
        """Mark entity as updated"""
        self.updated_at = datetime.now(timezone.utc)