"""
Authentication Service - Application Layer
Handles Google OAuth2, JWT token generation, and user authentication logic
"""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from app.shared.logging import get_logger, log_auth_event, log_error
from app.domain.entities.user import User, UserStatus, UserRole
from app.domain.repositories.user_repository import IUserRepository
from app.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    UserNotFoundError,
    InvalidTokenError,
)

logger = get_logger(__name__)


class AuthenticationService:
    """Authentication service handling OAuth2 and JWT operations"""

    def __init__(
        self,
        user_repository: IUserRepository,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        jwt_expiration_hours: int = 24,
        google_client_id: str = "",
        google_client_secret: str = "",
    ):
        self.user_repository = user_repository
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expiration_hours = jwt_expiration_hours
        self.google_client_id = google_client_id
        self.google_client_secret = google_client_secret

    async def authenticate_with_google(
        self, google_token: str, google_user_info: Dict[str, Any]
    ) -> tuple[User, str, str]:
        """
        Authenticate user with Google OAuth2
        Returns: (user, access_token, refresh_token)
        """
        try:
            # Extract user info from Google
            email = google_user_info.get("email")
            google_id = google_user_info.get("id") or google_user_info.get("sub")
            first_name = google_user_info.get("given_name", "")
            last_name = google_user_info.get("family_name", "")
            avatar_url = google_user_info.get("picture", "")
            email_verified = google_user_info.get("email_verified", False)

            if not email or not google_id:
                logger.warning(
                    "Invalid Google user information provided",
                    extra={"email": email, "google_id": google_id},
                )
                raise AuthenticationError("Invalid Google user information")

            logger.info(
                "Processing Google authentication",
                extra={"email": email, "google_id": google_id},
            )

            # Check if user exists
            existing_user = await self.user_repository.get_by_google_id(google_id)

            if existing_user:
                logger.info(
                    "Existing user found, updating login info",
                    extra={"user_id": str(existing_user.user_id)},
                )
                # Update last login and user info
                existing_user.mark_login()
                if email_verified and not existing_user.email_verified:
                    existing_user.verify_email()
                    logger.info(
                        "Email verified for existing user",
                        extra={"user_id": str(existing_user.user_id)},
                    )

                # Update profile if needed
                profile_updates = {}
                if first_name and not existing_user.profile.first_name:
                    profile_updates["first_name"] = first_name
                if last_name and not existing_user.profile.last_name:
                    profile_updates["last_name"] = last_name
                if avatar_url and not existing_user.profile.avatar_url:
                    profile_updates["avatar_url"] = avatar_url

                if profile_updates:
                    existing_user.update_profile(profile_updates)
                    logger.info(
                        "Updated user profile",
                        extra={
                            "user_id": str(existing_user.user_id),
                            "updates": profile_updates,
                        },
                    )

                user = await self.user_repository.update(existing_user)
            else:
                logger.info(
                    "Creating new user", extra={"email": email, "google_id": google_id}
                )
                # Create new user
                from app.domain.entities.user import UserProfile

                profile = UserProfile(
                    first_name=first_name, last_name=last_name, avatar_url=avatar_url
                )

                user = User(
                    user_id=uuid4(),
                    email=email,
                    google_id=google_id,
                    status=UserStatus.ACTIVE,
                    role=UserRole.USER,
                    profile=profile,
                    email_verified=email_verified,
                    terms_accepted_at=datetime.now(timezone.utc),
                    privacy_accepted_at=datetime.now(timezone.utc),
                )

                user = await self.user_repository.create(user)
                logger.info(
                    "New user created successfully",
                    extra={"user_id": str(user.user_id), "email": user.email},
                )

            # Generate tokens
            access_token = self._generate_access_token(user)
            refresh_token = self._generate_refresh_token(user)

            log_auth_event(logger, "google_auth_success", user_id=str(user.user_id))

            return user, access_token, refresh_token

        except Exception as e:
            log_error(logger, e, context="google_authentication")
            raise AuthenticationError(f"Google authentication failed: {str(e)}")

    async def authenticate_with_jwt(self, token: str) -> User:
        """Authenticate user with JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={"verify_aud": False, "verify_iss": False},
            )

            user_id = UUID(payload.get("user_id"))
            token_type = payload.get("type")

            if token_type != "access":
                raise InvalidTokenError("Invalid token type")

            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            if user.status != UserStatus.ACTIVE:
                raise AuthorizationError("User account is not active")

            return user

        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")
        except Exception as e:
            raise AuthenticationError(f"JWT authentication failed: {str(e)}")

    async def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(
                refresh_token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )

            user_id = UUID(payload.get("user_id"))
            token_type = payload.get("type")

            if token_type != "refresh":
                raise InvalidTokenError("Invalid token type")

            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"User {user_id} not found")

            if user.status != UserStatus.ACTIVE:
                raise AuthorizationError("User account is not active")

            # Generate new tokens
            new_access_token = self._generate_access_token(user)
            new_refresh_token = self._generate_refresh_token(user)

            return new_access_token, new_refresh_token

        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Refresh token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid refresh token")
        except Exception as e:
            raise AuthenticationError(f"Token refresh failed: {str(e)}")

    def _generate_access_token(self, user: User) -> str:
        """Generate JWT access token"""
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(hours=self.jwt_expiration_hours)

        payload = {
            "user_id": str(user.user_id),
            "email": user.email,
            "role": user.role.value,
            "subscription_tier": user.subscription.tier.value,
            "type": "access",
            "iat": now,
            "exp": expiry,
            "iss": "sdcoach-api",
            "aud": "sdcoach-app",
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def _generate_refresh_token(self, user: User) -> str:
        """Generate JWT refresh token"""
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(days=30)  # Refresh tokens last 30 days

        payload = {
            "user_id": str(user.user_id),
            "type": "refresh",
            "iat": now,
            "exp": expiry,
            "iss": "sdcoach-api",
            "aud": "sdcoach-app",
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_token_signature(self, token: str) -> bool:
        """Verify token signature without decoding"""
        try:
            jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={"verify_exp": False},
            )
            return True
        except jwt.InvalidTokenError:
            return False

    def extract_user_id_from_token(self, token: str) -> Optional[UUID]:
        """Extract user ID from token without full validation"""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={"verify_exp": False},
            )
            return UUID(payload.get("user_id"))
        except:
            return None
