"""
User API Endpoints - Authentication and User Management
Handles Google OAuth2, JWT authentication, and user operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from typing import Optional
import httpx
import os
from uuid import UUID

from app.shared.logging import get_logger, log_endpoint_call, log_auth_event, log_error
from app.application.services.auth_service import AuthenticationService
from app.domain.repositories.user_repository import IUserRepository
from app.interfaces.schemas.user_schemas import (
    UserResponse,
    UserProfileUpdate,
    UserPreferencesUpdate,
    TokenResponse,
    GoogleAuthRequest,
    RefreshTokenRequest,
)
from app.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    UserNotFoundError,
    InvalidTokenError,
)


# Router setup
router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer(auto_error=False)
logger = get_logger(__name__)


# Import the actual dependency injection functions from main
from app.infrastructure.database.repositories.user_repository_impl import (
    PostgreSQLUserRepository,
)
from app.infrastructure.database.config import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
import os


# Dependency injection functions
async def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PostgreSQLUserRepository:
    """Get user repository instance"""
    return PostgreSQLUserRepository(session)


async def get_auth_service(
    user_repository: PostgreSQLUserRepository = Depends(get_user_repository),
) -> AuthenticationService:
    """Get authentication service instance"""
    return AuthenticationService(
        user_repository=user_repository,
        jwt_secret=os.getenv("JWT_SECRET_KEY", "dev-secret-key"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = await auth_service.authenticate_with_jwt(credentials.credentials)
        return user
    except (InvalidTokenError, AuthenticationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.post("/auth/google", response_model=TokenResponse)
async def authenticate_with_google(
    auth_request: GoogleAuthRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """
    Authenticate user with Google OAuth2

    Steps:
    1. Verify Google token
    2. Extract user information
    3. Create or update user
    4. Generate JWT tokens
    """
    log_endpoint_call(logger, "/users/auth/google", "POST")

    try:
        # Check if this is a development mock token
        is_dev_mode = os.getenv("ENVIRONMENT", "production") == "development"

        if is_dev_mode and auth_request.access_token.startswith("eyJ"):
            # This is likely a mock JWT token for development
            try:
                import jwt

                # Decode the mock token to get user info
                mock_payload = jwt.decode(
                    auth_request.access_token, options={"verify_signature": False}
                )

                google_user_info = {
                    "id": mock_payload.get("sub"),
                    "email": mock_payload.get("email"),
                    "given_name": mock_payload.get("given_name"),
                    "family_name": mock_payload.get("family_name"),
                    "picture": mock_payload.get("picture"),
                    "email_verified": True,
                }

                logger.info("Using mock token for development authentication")

            except Exception as e:
                log_error(logger, e, context="mock_token_decode")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid mock token: {str(e)}",
                )
        else:
            # Production: Verify with Google API
            logger.info("Verifying token with Google API")
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://www.googleapis.com/oauth2/v1/userinfo",
                    headers={"Authorization": f"Bearer {auth_request.access_token}"},
                )

                if response.status_code != 200:
                    logger.warning(
                        "Google token verification failed",
                        extra={"status_code": response.status_code},
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Google token",
                    )

                google_user_info = response.json()
                logger.info(
                    "Google token verified successfully",
                    extra={"email": google_user_info.get("email")},
                )

        # Authenticate with our service
        user, access_token, refresh_token = await auth_service.authenticate_with_google(
            auth_request.access_token, google_user_info
        )

        log_auth_event(logger, "google_auth_success", user_id=str(user.user_id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=86400,  # 24 hours
            user=UserResponse.from_entity(user),
        )

    except AuthenticationError as e:
        log_error(logger, e, context="google_authentication")
        log_auth_event(logger, "google_auth_failure", error=str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        log_error(logger, e, context="google_authentication")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
    user_repository: IUserRepository = Depends(get_user_repository),
):
    """Refresh access token using refresh token"""
    try:
        access_token, refresh_token = await auth_service.refresh_access_token(
            refresh_request.refresh_token
        )

        # Get user info for response
        user_id = auth_service.extract_user_id_from_token(access_token)
        user = await user_repository.get_by_id(user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=86400,
            user=UserResponse.from_entity(user),
        )

    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user=Depends(get_current_user)):
    """Get current user's profile"""
    return UserResponse.from_entity(current_user)


@router.put("/me/profile", response_model=UserResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user=Depends(get_current_user),
    user_repository: IUserRepository = Depends(get_user_repository),
):
    """Update current user's profile"""
    try:
        # Update profile
        current_user.update_profile(profile_update.dict(exclude_unset=True))

        # Save to database
        updated_user = await user_repository.update(current_user)

        return UserResponse.from_entity(updated_user)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}",
        )


@router.put("/me/preferences", response_model=UserResponse)
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user=Depends(get_current_user),
    user_repository: IUserRepository = Depends(get_user_repository),
):
    """Update current user's preferences"""
    try:
        # Update preferences
        current_user.update_preferences(preferences_update.dict(exclude_unset=True))

        # Save to database
        updated_user = await user_repository.update(current_user)

        return UserResponse.from_entity(updated_user)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preferences update failed: {str(e)}",
        )


@router.post("/me/subscription/upgrade")
async def upgrade_subscription(
    tier: str,
    duration_months: int = 1,
    current_user=Depends(get_current_user),
    user_repository: IUserRepository = Depends(get_user_repository),
):
    """Upgrade user subscription - ready for payment integration"""
    try:
        from app.domain.entities.user import SubscriptionTier

        # Validate tier
        try:
            subscription_tier = SubscriptionTier(tier)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription tier: {tier}",
            )

        # TODO: Integrate with payment processor (Stripe)
        # For MVP, we'll just upgrade without payment

        current_user.upgrade_subscription(subscription_tier, duration_months)
        updated_user = await user_repository.update(current_user)

        return {
            "message": "Subscription upgraded successfully",
            "user": UserResponse.from_entity(updated_user),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subscription upgrade failed: {str(e)}",
        )


@router.post("/me/subscription/trial")
async def start_trial(
    tier: str,
    trial_days: int = 14,
    current_user=Depends(get_current_user),
    user_repository: IUserRepository = Depends(get_user_repository),
):
    """Start trial subscription"""
    try:
        from app.domain.entities.user import SubscriptionTier

        # Validate tier
        try:
            subscription_tier = SubscriptionTier(tier)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription tier: {tier}",
            )

        # Check if user already had a trial
        if current_user.subscription.is_trial:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already used trial period",
            )

        current_user.start_trial(subscription_tier, trial_days)
        updated_user = await user_repository.update(current_user)

        return {
            "message": "Trial started successfully",
            "user": UserResponse.from_entity(updated_user),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trial start failed: {str(e)}",
        )


@router.delete("/me")
async def deactivate_account(
    current_user=Depends(get_current_user),
    user_repository: IUserRepository = Depends(get_user_repository),
):
    """Deactivate current user's account"""
    try:
        current_user.deactivate("User requested account deactivation")
        await user_repository.update(current_user)

        return {"message": "Account deactivated successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account deactivation failed: {str(e)}",
        )


@router.post("/auth/logout")
async def logout(current_user=Depends(get_current_user)):
    """Logout user (client should discard tokens)"""
    # In a more sophisticated setup, we could maintain a token blacklist
    # For now, we rely on client-side token removal
    return {"message": "Logged out successfully"}


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    log_endpoint_call(logger, "/users/health", "GET")
    return {"status": "healthy", "service": "user-service"}


# Simple test endpoint
@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    log_endpoint_call(logger, "/users/test", "GET")
    return {"message": "Test endpoint working!", "timestamp": "2025-08-27"}


# Development-only endpoint for easy testing
@router.post("/auth/dev-login", response_model=TokenResponse)
async def dev_login(
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """Development-only login endpoint that creates/logs in a test user"""
    log_endpoint_call(logger, "/users/auth/dev-login", "POST")

    # Only allow in development
    environment = os.getenv("ENVIRONMENT", "production")
    logger.info(f"Dev login attempt", extra={"environment": environment})

    if environment != "development":
        logger.warning("Dev login endpoint accessed in non-development environment")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available in production",
        )

    try:
        logger.info("Starting dev login authentication process")

        # Mock Google user info for development
        google_user_info = {
            "id": "dev_user_123",
            "email": "dev@example.com",
            "given_name": "Dev",
            "family_name": "User",
            "picture": "https://example.com/avatar.jpg",
            "email_verified": True,
        }

        logger.info(
            "Using mock user data for development login",
            extra={"email": google_user_info["email"]},
        )

        # Authenticate with our service
        user, access_token, refresh_token = await auth_service.authenticate_with_google(
            "mock_token", google_user_info
        )

        log_auth_event(logger, "dev_login_success", user_id=str(user.user_id))
        logger.info(
            "Dev login authentication successful",
            extra={
                "user_id": str(user.user_id),
                "email": user.email,
                "access_token_length": len(access_token),
                "refresh_token_length": len(refresh_token),
            },
        )

        response = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=86400,
            user=UserResponse.from_entity(user),
        )

        return response

    except Exception as e:
        log_error(logger, e, context="dev_login")
        log_auth_event(logger, "dev_login_failure", error=str(e))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dev login failed: {str(e)}",
        )
