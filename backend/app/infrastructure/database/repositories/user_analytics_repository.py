"""
SQLAlchemy implementation of UserAnalytics Repository
"""

from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.domain.entities.user_analytics import UserAnalytics
from app.domain.repositories.user_analytics_repository import UserAnalyticsRepository
from app.infrastructure.database.models.user_analytics_model import UserAnalyticsModel
from app.shared.exceptions import (
    DatabaseError,
    ResourceNotFoundError,
)
from app.shared.logging import get_logger

logger = get_logger(__name__)


class SQLAlchemyUserAnalyticsRepository(UserAnalyticsRepository):
    """SQLAlchemy implementation of user analytics repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserAnalytics]:
        """Get user analytics by user ID"""
        try:
            # Use a more specific column selection to handle missing columns gracefully
            from sqlalchemy import text
            
            # Try with new columns first, fallback if they don't exist
            try:
                stmt = select(UserAnalyticsModel).where(UserAnalyticsModel.user_id == user_id)
                result = await self.session.execute(stmt)
                model = result.scalar_one_or_none()
                
                if model:
                    return self._model_to_entity(model)
                return None
                
            except SQLAlchemyError as column_error:
                if "does not exist" in str(column_error):
                    # Fallback to basic columns only
                    logger.warning(f"Some columns missing, using fallback query: {column_error}")
                    
                    fallback_query = text("""
                        SELECT id, user_id, avg_score, streak, interviews_left, 
                               interviews_this_month, interviews_today, last_interview_date, updated_at
                        FROM user_analytics 
                        WHERE user_id = :user_id
                    """)
                    
                    result = await self.session.execute(fallback_query, {"user_id": user_id})
                    row = result.fetchone()
                    
                    if row:
                        # Create a UserAnalytics entity with fallback values for missing fields
                        return UserAnalytics(
                            id=row.id,
                            user_id=row.user_id,
                            avg_score=float(row.avg_score) if row.avg_score else None,
                            streak=row.streak,
                            best_streak=0,  # Default fallback
                            total_interviews=0,  # Default fallback
                            interviews_left=row.interviews_left,
                            interviews_this_month=row.interviews_this_month,
                            interviews_today=row.interviews_today,
                            last_interview_date=row.last_interview_date,
                            updated_at=row.updated_at,
                        )
                    return None
                else:
                    raise column_error

        except SQLAlchemyError as e:
            logger.error(f"Database error getting user analytics: {e}")
            raise DatabaseError(f"Failed to get user analytics: {e}")

    async def create(self, analytics: UserAnalytics) -> UserAnalytics:
        """Create new user analytics record"""
        try:
            model = self._entity_to_model(analytics)
            self.session.add(model)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(model)
            
            logger.info(f"User analytics created for user_id: {analytics.user_id}")
            return self._model_to_entity(model)

        except SQLAlchemyError as e:
            logger.error(f"Database error creating user analytics: {e}")
            raise DatabaseError(f"Failed to create user analytics: {e}")

    async def update(self, analytics: UserAnalytics) -> UserAnalytics:
        """Update user analytics record"""
        try:
            stmt = select(UserAnalyticsModel).where(UserAnalyticsModel.user_id == analytics.user_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                raise ResourceNotFoundError(f"User analytics not found for user_id: {analytics.user_id}")

            # Update model fields
            model.avg_score = analytics.avg_score
            model.streak = analytics.streak
            model.best_streak = analytics.best_streak
            model.total_interviews = analytics.total_interviews
            model.interviews_left = analytics.interviews_left
            model.interviews_this_month = analytics.interviews_this_month
            model.interviews_today = analytics.interviews_today
            model.last_interview_date = analytics.last_interview_date
            model.updated_at = analytics.updated_at

            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(model)

            logger.info(f"User analytics updated for user_id: {analytics.user_id}")
            return self._model_to_entity(model)

        except SQLAlchemyError as e:
            logger.error(f"Database error updating user analytics: {e}")
            raise DatabaseError(f"Failed to update user analytics: {e}")

    async def get_or_create(self, user_id: uuid.UUID) -> UserAnalytics:
        """Get existing analytics or create new one for user"""
        existing = await self.get_by_user_id(user_id)
        if existing:
            return existing

        # Create new analytics record
        new_analytics = UserAnalytics(user_id=user_id)
        return await self.create(new_analytics)

    async def delete(self, user_id: uuid.UUID) -> bool:
        """Delete user analytics record"""
        try:
            stmt = select(UserAnalyticsModel).where(UserAnalyticsModel.user_id == user_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                return False

            await self.session.delete(model)
            await self.session.flush()
            await self.session.commit()

            logger.info(f"User analytics deleted for user_id: {user_id}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Database error deleting user analytics: {e}")
            raise DatabaseError(f"Failed to delete user analytics: {e}")

    def _entity_to_model(self, analytics: UserAnalytics) -> UserAnalyticsModel:
        """Convert domain entity to SQLAlchemy model"""
        return UserAnalyticsModel(
            id=analytics.id,
            user_id=analytics.user_id,
            avg_score=analytics.avg_score,
            streak=analytics.streak,
            best_streak=getattr(analytics, 'best_streak', 0),
            total_interviews=getattr(analytics, 'total_interviews', 0),
            interviews_left=analytics.interviews_left,
            interviews_this_month=analytics.interviews_this_month,
            interviews_today=analytics.interviews_today,
            last_interview_date=analytics.last_interview_date,
            updated_at=analytics.updated_at,
        )

    def _model_to_entity(self, model: UserAnalyticsModel) -> UserAnalytics:
        """Convert SQLAlchemy model to domain entity"""
        return UserAnalytics(
            id=model.id,
            user_id=model.user_id,
            avg_score=float(model.avg_score) if model.avg_score else None,
            streak=model.streak,
            best_streak=getattr(model, 'best_streak', 0),
            total_interviews=getattr(model, 'total_interviews', 0),
            interviews_left=model.interviews_left,
            interviews_this_month=model.interviews_this_month,
            interviews_today=model.interviews_today,
            last_interview_date=model.last_interview_date,
            updated_at=model.updated_at,
        )