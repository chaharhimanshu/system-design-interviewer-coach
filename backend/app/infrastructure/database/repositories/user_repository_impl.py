"""
User Repository Implementation - PostgreSQL with SQLAlchemy
Implements the user repository interface for database operations
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.exc import IntegrityError

from app.domain.entities.user import User, UserStatus
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.database.models.user_model import UserModel
from app.shared.exceptions import DatabaseError, UserNotFoundError


class PostgreSQLUserRepository(IUserRepository):
    """PostgreSQL implementation of user repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> User:
        """Create a new user"""
        try:
            user_model = UserModel.from_entity(user)
            self.session.add(user_model)
            await self.session.commit()
            await self.session.refresh(user_model)

            return user_model.to_entity()

        except IntegrityError as e:
            await self.session.rollback()
            if "email" in str(e):
                raise DatabaseError("User with this email already exists")
            elif "google_id" in str(e):
                raise DatabaseError("User with this Google ID already exists")
            else:
                raise DatabaseError(f"Database integrity error: {str(e)}")
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to create user: {str(e)}")

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        try:
            query = select(UserModel).where(UserModel.id == user_id)
            result = await self.session.execute(query)
            user_model = result.scalar_one_or_none()

            return user_model.to_entity() if user_model else None

        except Exception as e:
            raise DatabaseError(f"Failed to get user by ID: {str(e)}")

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            query = select(UserModel).where(UserModel.email == email)
            result = await self.session.execute(query)
            user_model = result.scalar_one_or_none()

            return user_model.to_entity() if user_model else None

        except Exception as e:
            raise DatabaseError(f"Failed to get user by email: {str(e)}")

    async def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID"""
        try:
            query = select(UserModel).where(UserModel.google_id == google_id)
            result = await self.session.execute(query)
            user_model = result.scalar_one_or_none()

            return user_model.to_entity() if user_model else None

        except Exception as e:
            raise DatabaseError(f"Failed to get user by Google ID: {str(e)}")

    async def update(self, user: User) -> User:
        """Update existing user"""
        try:
            # First get the existing model
            query = select(UserModel).where(UserModel.id == user.user_id)
            result = await self.session.execute(query)
            user_model = result.scalar_one_or_none()

            if not user_model:
                raise UserNotFoundError(f"User {user.user_id} not found")

            # Update the model with entity data
            user_model.update_from_entity(user)

            # Commit changes
            await self.session.commit()
            await self.session.refresh(user_model)

            return user_model.to_entity()

        except UserNotFoundError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to update user: {str(e)}")

    async def delete(self, user_id: UUID) -> bool:
        """Delete user (soft delete by setting status to DELETED)"""
        try:
            query = (
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(status=UserStatus.DELETED)
            )
            result = await self.session.execute(query)
            await self.session.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete user: {str(e)}")

    async def list_users(
        self,
        offset: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        subscription_tier: Optional[str] = None,
    ) -> List[User]:
        """List users with pagination and filters"""
        try:
            query = select(UserModel)

            # Apply filters
            if status:
                query = query.where(UserModel.status == UserStatus(status))

            if subscription_tier:
                query = query.where(
                    UserModel.subscription_data["tier"].astext == subscription_tier
                )

            # Apply pagination
            query = query.offset(offset).limit(limit)

            # Order by created_at desc
            query = query.order_by(UserModel.created_at.desc())

            result = await self.session.execute(query)
            user_models = result.scalars().all()

            return [user_model.to_entity() for user_model in user_models]

        except Exception as e:
            raise DatabaseError(f"Failed to list users: {str(e)}")

    async def count_users(
        self, status: Optional[str] = None, subscription_tier: Optional[str] = None
    ) -> int:
        """Count users with filters"""
        try:
            query = select(func.count(UserModel.id))

            # Apply filters
            if status:
                query = query.where(UserModel.status == UserStatus(status))

            if subscription_tier:
                query = query.where(
                    UserModel.subscription_data["tier"].astext == subscription_tier
                )

            result = await self.session.execute(query)
            return result.scalar()

        except Exception as e:
            raise DatabaseError(f"Failed to count users: {str(e)}")

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email"""
        try:
            query = select(func.count(UserModel.id)).where(UserModel.email == email)
            result = await self.session.execute(query)
            count = result.scalar()

            return count > 0

        except Exception as e:
            raise DatabaseError(f"Failed to check user existence by email: {str(e)}")

    async def get_active_users(self) -> List[User]:
        """Get all active users"""
        try:
            query = select(UserModel).where(UserModel.status == UserStatus.ACTIVE)
            result = await self.session.execute(query)
            user_models = result.scalars().all()

            return [user_model.to_entity() for user_model in user_models]

        except Exception as e:
            raise DatabaseError(f"Failed to get active users: {str(e)}")

    async def get_users_by_subscription_tier(self, tier: str) -> List[User]:
        """Get users by subscription tier (additional method)"""
        try:
            query = select(UserModel).where(
                UserModel.subscription_data["tier"].astext == tier
            )
            result = await self.session.execute(query)
            user_models = result.scalars().all()

            return [user_model.to_entity() for user_model in user_models]

        except Exception as e:
            raise DatabaseError(f"Failed to get users by subscription tier: {str(e)}")

    async def search_users(self, search_term: str, limit: int = 10) -> List[User]:
        """Search users by name or email (additional method)"""
        try:
            search_pattern = f"%{search_term}%"
            query = (
                select(UserModel)
                .where(
                    and_(
                        UserModel.status == UserStatus.ACTIVE,
                        (
                            UserModel.email.ilike(search_pattern)
                            | UserModel.first_name.ilike(search_pattern)
                            | UserModel.last_name.ilike(search_pattern)
                        ),
                    )
                )
                .limit(limit)
            )

            result = await self.session.execute(query)
            user_models = result.scalars().all()

            return [user_model.to_entity() for user_model in user_models]

        except Exception as e:
            raise DatabaseError(f"Failed to search users: {str(e)}")
