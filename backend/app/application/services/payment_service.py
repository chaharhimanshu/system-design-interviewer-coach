"""
Payment Service - Application Layer
Handles Razorpay integration and payment business logic
"""

import hashlib
import hmac
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone

import razorpay
from razorpay.errors import BadRequestError, ServerError

from app.domain.entities.payment import (
    Payment,
    Coupon,
    PaymentStatus,
    SubscriptionType,
    RazorpayPaymentDetails,
)
from app.domain.repositories.payment_repository import (
    IPaymentRepository,
    ICouponRepository,
)
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.config.settings import RazorpaySettings
from app.shared.logging import get_logger
from app.shared.exceptions import (
    ValidationError,
    BusinessRuleError,
    ExternalServiceError,
    ResourceNotFoundError,
)

logger = get_logger(__name__)


class PaymentService:
    """
    Payment service for Razorpay integration
    Handles order creation, payment verification, and coupon management
    """

    def __init__(
        self,
        payment_repository: IPaymentRepository,
        coupon_repository: ICouponRepository,
        user_repository: IUserRepository,
        razorpay_settings: RazorpaySettings,
    ):
        self.payment_repository = payment_repository
        self.coupon_repository = coupon_repository
        self.user_repository = user_repository
        self.razorpay_settings = razorpay_settings

        # Initialize Razorpay client
        self.razorpay_client = razorpay.Client(
            auth=(razorpay_settings.key_id, razorpay_settings.key_secret)
        )

    async def create_payment_order(
        self,
        user_id: UUID,
        subscription_type: SubscriptionType,
        coupon_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create Razorpay payment order for subscription
        """
        logger.info(
            f"Creating payment order for user {user_id}, subscription: {subscription_type}"
        )

        try:
            # Get user to validate
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise ResourceNotFoundError(f"User not found: {user_id}")

            # Determine amount based on subscription type
            if subscription_type == SubscriptionType.LIFETIME:
                amount = Decimal(str(self.razorpay_settings.lifetime_price_inr))
            else:  # MONTHLY
                amount = Decimal(str(self.razorpay_settings.monthly_price_inr))

            original_amount = amount
            coupon_applied = None
            discount_amount = Decimal("0")

            # Apply coupon if provided
            if coupon_code:
                coupon = await self.coupon_repository.get_by_code(coupon_code.upper())
                if not coupon:
                    raise ValidationError(f"Invalid coupon code: {coupon_code}")

                # Validate coupon
                is_valid, message = coupon.is_valid_for_amount(amount)
                if not is_valid:
                    raise ValidationError(f"Coupon validation failed: {message}")

                # Calculate discount
                discount_amount = coupon.calculate_discount(amount)
                amount = amount - discount_amount
                coupon_applied = coupon.coupon_id

                logger.info(
                    f"Coupon applied: {coupon_code}, discount: ₹{discount_amount}"
                )

            # Create Razorpay order
            order_amount_paise = int(amount * 100)  # Convert to paise
            order_receipt = f"{self.razorpay_settings.receipt_prefix}{user_id}_{int(datetime.now().timestamp())}"

            razorpay_order = self.razorpay_client.order.create(
                {
                    "amount": order_amount_paise,
                    "currency": self.razorpay_settings.currency,
                    "receipt": order_receipt,
                    "notes": {
                        "user_id": str(user_id),
                        "subscription_type": subscription_type.value,
                        "coupon_applied": coupon_code if coupon_code else "",
                        "original_amount": str(original_amount),
                        "discount_amount": str(discount_amount),
                    },
                }
            )

            # Create payment entity
            payment = Payment.create_for_subscription(
                user_id=user_id,
                subscription_type=subscription_type,
                amount=amount,
                order_id=razorpay_order["id"],
                receipt=order_receipt,
            )

            # Set original amount and discount if coupon applied
            if coupon_applied:
                payment.original_amount = original_amount
                payment.discount_amount = discount_amount
                payment.coupon_applied = coupon_applied

            # Save payment record
            await self.payment_repository.create(payment)

            logger.info(f"Payment order created: {razorpay_order['id']}")

            return {
                "order_id": razorpay_order["id"],
                "amount": int(amount * 100),  # Return in paise for frontend
                "currency": self.razorpay_settings.currency,
                "key": self.razorpay_settings.key_id,
                "name": "System Design Interview Coach",
                "description": f"{subscription_type.value.title()} Subscription",
                "prefill": {
                    "name": f"{user.profile.first_name or ''} {user.profile.last_name or ''}".strip(),
                    "email": user.email,
                    "contact": user.profile.phone_number or "",
                },
                "notes": razorpay_order["notes"],
                "theme": {"color": "#3399cc"},
                "discount_info": (
                    {
                        "original_amount": float(original_amount),
                        "discount_amount": float(discount_amount),
                        "final_amount": float(amount),
                        "coupon_code": coupon_code,
                        "savings_text": (
                            f"You saved ₹{discount_amount}"
                            if discount_amount > 0
                            else None
                        ),
                    }
                    if coupon_applied
                    else None
                ),
            }

        except razorpay.errors.BadRequestError as e:
            logger.error(f"Razorpay order creation failed: {str(e)}")
            raise ExternalServiceError(f"Payment service error: {str(e)}")
        except Exception as e:
            logger.error(f"Order creation failed: {str(e)}")
            raise

    async def verify_payment(
        self, razorpay_payment_id: str, razorpay_order_id: str, razorpay_signature: str
    ) -> Dict[str, Any]:
        """
        Verify Razorpay payment and update user subscription
        """
        logger.info(f"Verifying payment: {razorpay_payment_id}")

        try:
            # Verify signature
            if not self._verify_razorpay_signature(
                razorpay_order_id, razorpay_payment_id, razorpay_signature
            ):
                raise ValidationError("Invalid payment signature")

            # Get payment record
            payment = await self.payment_repository.get_by_order_id(razorpay_order_id)
            if not payment:
                raise ResourceNotFoundError(
                    f"Payment not found for order: {razorpay_order_id}"
                )

            # Get payment details from Razorpay
            try:
                razorpay_payment = self.razorpay_client.payment.fetch(
                    razorpay_payment_id
                )
                payment_method = razorpay_payment.get("method", "unknown")

            except Exception as e:
                logger.error(f"Failed to fetch payment details: {str(e)}")
                payment_method = "unknown"

            # Update payment as captured
            razorpay_details = RazorpayPaymentDetails(
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_signature=razorpay_signature,
            )

            payment.mark_as_authorized(razorpay_details)
            payment.mark_as_captured(payment_method)

            # Update payment in database
            await self.payment_repository.update(payment)

            # Update user subscription
            user = await self.user_repository.get_by_id(payment.user_id)
            if not user:
                raise ResourceNotFoundError(f"User not found: {payment.user_id}")

            # Upgrade user subscription
            is_lifetime = payment.subscription_type == SubscriptionType.LIFETIME
            user.upgrade_to_premium(
                is_lifetime=is_lifetime, payment_id=razorpay_payment_id
            )

            # Mark coupon as used if applied
            if payment.coupon_applied:
                coupon = await self.coupon_repository.get_by_id(payment.coupon_applied)
                if coupon:
                    coupon.use_coupon()
                    await self.coupon_repository.update(coupon)

            # Save user
            await self.user_repository.update(user)

            logger.info(
                f"Payment verified and subscription updated for user: {payment.user_id}"
            )

            return {
                "success": True,
                "payment_id": str(payment.payment_id),
                "subscription_type": payment.subscription_type.value,
                "amount_paid": payment.get_display_amount(),
                "subscription_active": True,
                "expires_at": (
                    user.subscription.expires_at.isoformat()
                    if user.subscription.expires_at
                    else None
                ),
                "discount_info": payment.get_discount_info(),
            }

        except Exception as e:
            # Mark payment as failed if it exists
            payment = await self.payment_repository.get_by_order_id(razorpay_order_id)
            if payment:
                payment.mark_as_failed(str(e))
                await self.payment_repository.update(payment)

            logger.error(f"Payment verification failed: {str(e)}")
            raise

    async def validate_coupon(
        self, coupon_code: str, amount: Decimal
    ) -> Dict[str, Any]:
        """
        Validate coupon code and return discount information
        """
        logger.info(f"Validating coupon: {coupon_code}")

        coupon = await self.coupon_repository.get_by_code(coupon_code.upper())
        if not coupon:
            raise ValidationError(f"Invalid coupon code: {coupon_code}")

        # Validate coupon
        is_valid, message = coupon.is_valid_for_amount(amount)
        if not is_valid:
            raise ValidationError(message)

        # Calculate discount
        discount_amount = coupon.calculate_discount(amount)
        final_amount = amount - discount_amount

        return {
            "valid": True,
            "coupon_code": coupon.code,
            "discount_type": coupon.coupon_type.value,
            "discount_value": float(coupon.discount_value),
            "original_amount": float(amount),
            "discount_amount": float(discount_amount),
            "final_amount": float(final_amount),
            "savings_text": f"You will save ₹{discount_amount}",
            "description": coupon.description,
        }

    async def get_user_payments(
        self, user_id: UUID, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get user's payment history
        """
        payments = await self.payment_repository.get_user_payments(user_id, limit=limit)

        return [
            {
                "payment_id": str(payment.payment_id),
                "order_id": payment.order_id,
                "amount": payment.get_display_amount(),
                "subscription_type": (
                    payment.subscription_type.value
                    if payment.subscription_type
                    else None
                ),
                "status": payment.status.value,
                "payment_method": (
                    payment.payment_method.value if payment.payment_method else None
                ),
                "created_at": payment.created_at.isoformat(),
                "discount_info": payment.get_discount_info(),
            }
            for payment in payments
        ]

    async def handle_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Handle Razorpay webhook events
        """
        logger.info("Processing Razorpay webhook")

        try:
            # Verify webhook signature
            if not self._verify_webhook_signature(payload, signature):
                logger.warning("Invalid webhook signature")
                return False

            event = payload.get("event")
            payment_data = (
                payload.get("payload", {}).get("payment", {}).get("entity", {})
            )

            if event == "payment.captured":
                await self._handle_payment_captured(payment_data)
            elif event == "payment.failed":
                await self._handle_payment_failed(payment_data)

            return True

        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return False

    def _verify_razorpay_signature(
        self, order_id: str, payment_id: str, signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature
        """
        try:
            # Create signature string
            signature_string = f"{order_id}|{payment_id}"

            # Generate expected signature
            expected_signature = hmac.new(
                self.razorpay_settings.key_secret.encode(),
                signature_string.encode(),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False

    def _verify_webhook_signature(
        self, payload: Dict[str, Any], signature: str
    ) -> bool:
        """
        Verify Razorpay webhook signature
        """
        try:
            import json

            # Convert payload to JSON string
            payload_string = json.dumps(payload, sort_keys=True, separators=(",", ":"))

            # Generate expected signature
            expected_signature = hmac.new(
                self.razorpay_settings.webhook_secret.encode(),
                payload_string.encode(),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False

    async def _handle_payment_captured(self, payment_data: Dict[str, Any]) -> None:
        """Handle payment captured webhook"""
        order_id = payment_data.get("order_id")
        if not order_id:
            return

        payment = await self.payment_repository.get_by_order_id(order_id)
        if payment and payment.status != PaymentStatus.CAPTURED:
            payment.mark_as_captured()
            await self.payment_repository.update(payment)
            logger.info(f"Payment captured via webhook: {order_id}")

    async def _handle_payment_failed(self, payment_data: Dict[str, Any]) -> None:
        """Handle payment failed webhook"""
        order_id = payment_data.get("order_id")
        error_reason = payment_data.get("error_description", "Payment failed")

        if not order_id:
            return

        payment = await self.payment_repository.get_by_order_id(order_id)
        if payment and payment.status not in [
            PaymentStatus.FAILED,
            PaymentStatus.CAPTURED,
        ]:
            payment.mark_as_failed(error_reason)
            await self.payment_repository.update(payment)
            logger.info(f"Payment failed via webhook: {order_id}")
