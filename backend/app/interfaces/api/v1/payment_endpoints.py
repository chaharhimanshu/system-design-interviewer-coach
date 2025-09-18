"""
Payment API Endpoints - Interface Layer
FastAPI routes for Razorpay payment integration
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from app.application.services.payment_service import PaymentService
from app.domain.entities.payment import SubscriptionType
from app.infrastructure.database.config import get_db_session
from app.domain.entities.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.logging import get_logger
from app.shared.exceptions import (
    ValidationError,
    BusinessRuleError,
    ExternalServiceError,
    ResourceNotFoundError,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


# Dependency injection functions
from app.infrastructure.database.repositories.user_repository_impl import (
    PostgreSQLUserRepository,
)
from app.infrastructure.database.repositories.payment_repository_impl import (
    PostgreSQLPaymentRepository,
    PostgreSQLCouponRepository,
)
from app.infrastructure.config.settings import get_settings
from app.application.services.auth_service import AuthenticationService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

security = HTTPBearer(auto_error=False)


async def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PostgreSQLUserRepository:
    """Get user repository instance"""
    return PostgreSQLUserRepository(session)


async def get_payment_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PostgreSQLPaymentRepository:
    """Get payment repository instance"""
    return PostgreSQLPaymentRepository(session)


async def get_coupon_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PostgreSQLCouponRepository:
    """Get coupon repository instance"""
    return PostgreSQLCouponRepository(session)


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


async def get_payment_service(
    payment_repository: PostgreSQLPaymentRepository = Depends(get_payment_repository),
    coupon_repository: PostgreSQLCouponRepository = Depends(get_coupon_repository),
    user_repository: PostgreSQLUserRepository = Depends(get_user_repository),
) -> PaymentService:
    """Get payment service instance"""
    settings = get_settings()
    return PaymentService(
        payment_repository=payment_repository,
        coupon_repository=coupon_repository,
        user_repository=user_repository,
        razorpay_settings=settings.razorpay,
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
        from app.shared.exceptions import InvalidTokenError, AuthenticationError

        user = await auth_service.authenticate_with_jwt(credentials.credentials)
        return user
    except (InvalidTokenError, AuthenticationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Request/Response Models
class CreateOrderRequest(BaseModel):
    subscription_type: SubscriptionType = Field(..., description="Subscription type")
    coupon_code: Optional[str] = Field(None, description="Optional coupon code")

    @validator("coupon_code")
    def validate_coupon_code(cls, v):
        if v:
            return v.strip().upper()
        return v


class PaymentVerificationRequest(BaseModel):
    razorpay_payment_id: str = Field(..., description="Razorpay payment ID")
    razorpay_order_id: str = Field(..., description="Razorpay order ID")
    razorpay_signature: str = Field(..., description="Razorpay signature")


class CouponValidationRequest(BaseModel):
    coupon_code: str = Field(..., description="Coupon code to validate")
    subscription_type: SubscriptionType = Field(
        ..., description="Subscription type for validation"
    )

    @validator("coupon_code")
    def validate_coupon_code(cls, v):
        return v.strip().upper()


class OrderResponse(BaseModel):
    success: bool
    order_details: Dict[str, Any]
    message: str


class PaymentVerificationResponse(BaseModel):
    success: bool
    payment_details: Dict[str, Any]
    message: str


class CouponValidationResponse(BaseModel):
    valid: bool
    discount_info: Optional[Dict[str, Any]]
    message: str


class PaymentHistoryResponse(BaseModel):
    success: bool
    payments: List[Dict[str, Any]]
    total_count: int


# Endpoints
@router.post("/create-order", response_model=OrderResponse)
async def create_payment_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Create Razorpay payment order for subscription
    """
    try:
        logger.info(
            f"Creating order for user {current_user.user_id}, type: {request.subscription_type}"
        )

        # Check if user is already premium
        if current_user.subscription and current_user.subscription.is_active:
            raise BusinessRuleError("User already has an active subscription")

        order_details = await payment_service.create_payment_order(
            user_id=current_user.user_id,
            subscription_type=request.subscription_type,
            coupon_code=request.coupon_code,
        )

        return OrderResponse(
            success=True,
            order_details=order_details,
            message="Payment order created successfully",
        )

    except ValidationError as e:
        logger.warning(f"Order creation validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except BusinessRuleError as e:
        logger.warning(f"Order creation business rule error: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except ExternalServiceError as e:
        logger.error(f"Razorpay service error: {str(e)}")
        raise HTTPException(
            status_code=502, detail="Payment service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/verify", response_model=PaymentVerificationResponse)
async def verify_payment(
    request: PaymentVerificationRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Verify Razorpay payment and activate subscription
    """
    try:
        logger.info(
            f"Verifying payment for user {current_user.user_id}: {request.razorpay_payment_id}"
        )

        payment_details = await payment_service.verify_payment(
            razorpay_payment_id=request.razorpay_payment_id,
            razorpay_order_id=request.razorpay_order_id,
            razorpay_signature=request.razorpay_signature,
        )

        return PaymentVerificationResponse(
            success=True,
            payment_details=payment_details,
            message="Payment verified and subscription activated successfully",
        )

    except ValidationError as e:
        logger.warning(f"Payment verification failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        logger.warning(f"Payment not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except ExternalServiceError as e:
        logger.error(f"Payment verification service error: {str(e)}")
        raise HTTPException(
            status_code=502, detail="Payment verification service unavailable"
        )
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate-coupon", response_model=CouponValidationResponse)
async def validate_coupon(
    request: CouponValidationRequest,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Validate coupon code and return discount information
    """
    try:
        logger.info(
            f"Validating coupon for user {current_user.user_id}: {request.coupon_code}"
        )

        # Determine amount based on subscription type
        from app.infrastructure.config.settings import get_settings

        settings = get_settings()

        if request.subscription_type == SubscriptionType.LIFETIME:
            amount = Decimal(str(settings.razorpay.lifetime_price_inr))
        else:  # MONTHLY
            amount = Decimal(str(settings.razorpay.monthly_price_inr))

        discount_info = await payment_service.validate_coupon(
            coupon_code=request.coupon_code, amount=amount
        )

        return CouponValidationResponse(
            valid=True, discount_info=discount_info, message="Coupon is valid"
        )

    except ValidationError as e:
        logger.warning(f"Coupon validation failed: {str(e)}")
        return CouponValidationResponse(valid=False, discount_info=None, message=str(e))
    except Exception as e:
        logger.error(f"Coupon validation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history", response_model=PaymentHistoryResponse)
async def get_payment_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Get user's payment history
    """
    try:
        logger.info(f"Fetching payment history for user {current_user.user_id}")

        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100")

        payments = await payment_service.get_user_payments(
            user_id=current_user.user_id, limit=limit
        )

        return PaymentHistoryResponse(
            success=True, payments=payments, total_count=len(payments)
        )

    except ValidationError as e:
        logger.warning(f"Payment history validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Payment history fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Handle Razorpay webhook events
    """
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("X-Razorpay-Signature")

        if not signature:
            logger.warning("Webhook received without signature")
            raise HTTPException(status_code=400, detail="Missing signature")

        # Parse JSON payload
        import json

        payload = json.loads(body.decode("utf-8"))

        logger.info(f"Received webhook event: {payload.get('event', 'unknown')}")

        # Process webhook in background
        background_tasks.add_task(
            process_webhook_background, payment_service, payload, signature
        )

        # Return success immediately
        return {"status": "ok"}

    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/subscription-status")
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """
    Get current user's subscription status
    """
    try:
        subscription = current_user.subscription

        if not subscription:
            return {
                "has_subscription": False,
                "is_active": False,
                "subscription_type": None,
                "expires_at": None,
                "interviews_remaining": max(0, 2 - current_user.interviews_this_month),
            }

        return {
            "has_subscription": True,
            "is_active": subscription.is_active,
            "subscription_type": (
                subscription.subscription_type.value
                if subscription.subscription_type
                else None
            ),
            "expires_at": (
                subscription.expires_at.isoformat() if subscription.expires_at else None
            ),
            "is_lifetime": subscription.is_lifetime,
            "interviews_remaining": (
                "unlimited"
                if subscription.is_active
                else max(0, 2 - current_user.interviews_this_month)
            ),
        }

    except Exception as e:
        logger.error(f"Subscription status fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pricing")
async def get_pricing_info():
    """
    Get current pricing information
    """
    try:
        from app.infrastructure.config.settings import get_settings

        settings = get_settings()

        return {
            "lifetime": {
                "price_inr": settings.razorpay.lifetime_price_inr,
                "price_display": f"₹{settings.razorpay.lifetime_price_inr}",
                "description": "One-time payment for lifetime access",
                "features": [
                    "Unlimited interviews",
                    "All system design topics",
                    "Detailed feedback and scoring",
                    "Performance analytics",
                    "Lifetime updates",
                ],
            },
            "monthly": {
                "price_inr": settings.razorpay.monthly_price_inr,
                "price_display": f"₹{settings.razorpay.monthly_price_inr}",
                "description": "Monthly subscription with auto-renewal",
                "features": [
                    "Unlimited interviews",
                    "All system design topics",
                    "Detailed feedback and scoring",
                    "Performance analytics",
                ],
            },
            "free": {
                "price_inr": 0,
                "price_display": "Free",
                "description": "Limited access for evaluation",
                "features": [
                    "2 interviews per month",
                    "Basic feedback",
                    "Core system design topics",
                ],
            },
            "currency": settings.razorpay.currency,
            "payment_methods": [
                "UPI",
                "Credit Card",
                "Debit Card",
                "Net Banking",
                "Wallet",
            ],
        }

    except Exception as e:
        logger.error(f"Pricing info fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Background task for webhook processing
async def process_webhook_background(
    payment_service: PaymentService, payload: Dict[str, Any], signature: str
):
    """
    Process webhook in background task
    """
    try:
        success = await payment_service.handle_webhook(payload, signature)
        if success:
            logger.info("Webhook processed successfully")
        else:
            logger.warning("Webhook processing failed")
    except Exception as e:
        logger.error(f"Background webhook processing error: {str(e)}")


# Health check endpoint
@router.get("/health")
async def payment_health_check():
    """
    Health check for payment service
    """
    try:
        from app.infrastructure.config.settings import get_settings

        settings = get_settings()

        # Basic configuration check
        razorpay_configured = bool(
            settings.razorpay.key_id and settings.razorpay.key_secret
        )

        return {
            "status": "healthy",
            "razorpay_configured": razorpay_configured,
            "pricing_configured": bool(
                settings.razorpay.lifetime_price_inr
                and settings.razorpay.monthly_price_inr
            ),
            "timestamp": "2025-09-17T00:00:00Z",
        }

    except Exception as e:
        logger.error(f"Payment health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2025-09-17T00:00:00Z",
            },
        )
