"""
Subscription API Endpoints - Interface Layer
FastAPI routes for subscription management
"""

import os
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

# FastAPI imports
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# SQLAlchemy imports
from sqlalchemy.ext.asyncio import AsyncSession

# Application layer imports
from app.application.services.subscription_service import SubscriptionService
from app.application.services.user_analytics_service import UserAnalyticsService
from app.application.services.user_service import UserService
from app.application.services.auth_service import AuthenticationService

# Domain layer imports
from app.domain.entities.user import User
from app.domain.repositories.user_subscription_repository import UserSubscriptionRepository

# Interfaces
from app.interfaces.api.v1.user_endpoints import get_current_user


# Infrastructure layer imports
from app.infrastructure.database.config import get_db_session
from app.infrastructure.database.repositories.user_subscription_repository import SQLAlchemyUserSubscriptionRepository
from app.infrastructure.database.repositories.user_repository_impl import PostgreSQLUserRepository
from app.infrastructure.database.repositories.user_analytics_repository import SQLAlchemyUserAnalyticsRepository

# Shared imports
from app.shared.logging import get_logger
from app.shared.exceptions import (
    BusinessRuleError,
    ResourceNotFoundError,
    ValidationError,
)

# Initialize logger and router
logger = get_logger(__name__)
router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# Security
security = HTTPBearer(auto_error=False)


# ================================
# Pydantic Models for Request/Response
# ================================
class CreateUserSubscriptionRequest(BaseModel):
    """Request model for creating user subscription"""
    user_id: UUID = Field(..., description="User ID")
    subscription_id: UUID = Field(..., description="Subscription plan ID")
    start_date: Optional[datetime] = Field(None, description="Subscription start date")
    end_date: Optional[datetime] = Field(None, description="Subscription end date")

class UserSubscriptionResponse(BaseModel):
    """Response model for user subscription details"""
    success: bool
    action: str = Field(..., description="Action taken: 'created' or 'updated'")
    user_id: str
    subscription_id: str
    start_date: str
    end_date: Optional[str]
    status: str

class SubscriptionDetailsResponse(BaseModel):
    """Response model for comprehensive subscription details"""
    # User info
    user_id: str
    email: str
    user_status: str
    
    # Subscription info
    subscription_tier: str
    subscription_active: bool
    subscription_expires_at: Optional[str]
    is_trial: bool
    auto_renew: bool
    
    # Interview limits and usage
    max_interviews_per_month: int
    interviews_used_this_month: int
    interviews_used_today: int
    remaining_interviews: Any  # int or "unlimited"
    can_create_interview: bool
    limit_reason: Optional[str]
    
    # Analytics
    avg_score: Optional[float]
    current_streak: int
    last_interview_date: Optional[str]
    
    # Metadata
    last_updated: str


# ================================
# Dependency Injection Functions
# ================================


async def get_subscription_service(
    db: AsyncSession = Depends(get_db_session),
) -> SubscriptionService:
    """Get subscription service with dependencies"""
    user_repository = PostgreSQLUserRepository(db)
    user_subscription_repository = SQLAlchemyUserSubscriptionRepository(db)
    analytics_repository = SQLAlchemyUserAnalyticsRepository(db)
    analytics_service = UserAnalyticsService(analytics_repository)
    
    return SubscriptionService(user_repository, user_subscription_repository, analytics_service)



# ================================
# API Endpoints
# ================================
@router.post("/user-subscription", response_model=UserSubscriptionResponse)
async def create_user_subscription(
    request: CreateUserSubscriptionRequest,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    current_user: User = Depends(get_current_user)  # Ensure user is authenticated
):
    """
    Create or update user subscription entry
    
    This endpoint creates a new entry in the user_subscription table linking
    a user to a subscription plan. If the user already has an active subscription,
    it will update the existing subscription instead of creating a duplicate entry.
    
    Returns:
    - action: "created" if a new subscription was created
    - action: "updated" if an existing subscription was modified
    """
    try:
        logger.info(f"Creating user subscription for user {request.user_id}")
        
        # Verify the requesting user has permission (admin or self)
        if current_user.user_id != request.user_id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create subscription for this user"
            )
        
        result = await subscription_service.create_user_subscription(
            user_id=request.user_id,
            subscription_id=request.subscription_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return UserSubscriptionResponse(**result)
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating user subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/details/{user_id}", response_model=SubscriptionDetailsResponse)
async def get_user_subscription_details(
    user_id: UUID,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive user subscription details
    
    This is the common function that joins user/subscription/user_subscription
    tables to fetch complete subscription and usage data.
    """
    try:
        logger.info(f"Getting subscription details for user {user_id}")
        
        # Verify the requesting user has permission (admin or self)
        if current_user.user_id != user_id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view subscription details for this user"
            )
        
        details = await subscription_service.get_user_subscription_details(user_id)
        
        return SubscriptionDetailsResponse(**details)
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting subscription details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/my-details", response_model=SubscriptionDetailsResponse)
async def get_my_subscription_details(
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's subscription details
    
    Convenience endpoint to get the authenticated user's own subscription details.
    """
    try:
        logger.info(f"Getting subscription details for current user {current_user.user_id}")
        
        details = await subscription_service.get_user_subscription_details(current_user.user_id)
        
        return SubscriptionDetailsResponse(**details)
        
    except BusinessRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting current user's subscription details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/check-permissions/{user_id}")
async def check_interview_permissions(
    user_id: UUID,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """
    Quick check for interview creation permissions
    
    Lightweight endpoint to check if a user can create new interviews
    without fetching all subscription details.
    """
    try:
        logger.info(f"Checking interview permissions for user {user_id}")
        
        # Verify the requesting user has permission (admin or self)
        if current_user.user_id != user_id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to check permissions for this user"
            )
        
        can_create, reason, summary = await subscription_service.check_interview_permissions(user_id)
        
        return {
            "user_id": str(user_id),
            "can_create_interview": can_create,
            "reason": reason if not can_create else "Allowed",
            "subscription_summary": summary,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error checking interview permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/check-my-permissions")
async def check_my_interview_permissions(
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """
    Quick check for current user's interview creation permissions
    """
    try:
        can_create, reason, summary = await subscription_service.check_interview_permissions(current_user.user_id)
        
        return {
            "user_id": str(current_user.user_id),
            "can_create_interview": can_create,
            "reason": reason if not can_create else "Allowed",
            "subscription_summary": summary,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Unexpected error checking current user's interview permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )