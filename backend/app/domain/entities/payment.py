"""
Payment Domain Entities
Core business logic for payment processing and subscription management
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum
from uuid import UUID, uuid4
from dataclasses import dataclass
from decimal import Decimal


class PaymentStatus(str, Enum):
    """Payment status enumeration"""

    CREATED = "created"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    REFUNDED = "refunded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment method enumeration"""

    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"


class SubscriptionType(str, Enum):
    """Subscription type enumeration"""

    MONTHLY = "monthly"
    LIFETIME = "lifetime"


class CouponType(str, Enum):
    """Coupon type enumeration"""

    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"


class CouponStatus(str, Enum):
    """Coupon status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    USED_UP = "used_up"


@dataclass
class PaymentOrderInfo:
    """Payment order information"""

    order_id: str
    amount: Decimal
    currency: str
    receipt: str
    status: str
    created_at: datetime


@dataclass
class RazorpayPaymentDetails:
    """Razorpay payment details"""

    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str


class Coupon:
    """
    Coupon domain entity
    Manages discount coupons with business rules
    """

    def __init__(
        self,
        coupon_id: UUID,
        code: str,
        coupon_type: CouponType,
        discount_value: Decimal,
        max_usage_count: int,
        current_usage_count: int = 0,
        valid_from: datetime = None,
        valid_until: datetime = None,
        minimum_amount: Optional[Decimal] = None,
        maximum_discount: Optional[Decimal] = None,
        status: CouponStatus = CouponStatus.ACTIVE,
        description: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.coupon_id = coupon_id
        self.code = code.upper()  # Business rule: codes are uppercase
        self.coupon_type = coupon_type
        self.discount_value = discount_value
        self.max_usage_count = max_usage_count
        self.current_usage_count = current_usage_count
        self.valid_from = valid_from or datetime.now(timezone.utc)
        self.valid_until = valid_until
        self.minimum_amount = minimum_amount
        self.maximum_discount = maximum_discount
        self.status = status
        self.description = description
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def is_valid_for_amount(self, amount: Decimal) -> tuple[bool, str]:
        """Check if coupon is valid for given amount"""

        # Check if coupon is active
        if self.status != CouponStatus.ACTIVE:
            return False, f"Coupon is {self.status.value}"

        # Check usage limit
        if self.current_usage_count >= self.max_usage_count:
            return False, "Coupon usage limit exceeded"

        # Check date validity
        now = datetime.now(timezone.utc)
        if self.valid_from and now < self.valid_from:
            return False, "Coupon is not yet valid"

        if self.valid_until and now > self.valid_until:
            return False, "Coupon has expired"

        # Check minimum amount
        if self.minimum_amount and amount < self.minimum_amount:
            return False, f"Minimum amount ₹{self.minimum_amount} required"

        return True, "Valid"

    def calculate_discount(self, amount: Decimal) -> Decimal:
        """Calculate discount amount for given total"""

        if self.coupon_type == CouponType.FIXED_AMOUNT:
            discount = self.discount_value
        else:  # PERCENTAGE
            discount = (amount * self.discount_value) / 100

        # Apply maximum discount limit
        if self.maximum_discount and discount > self.maximum_discount:
            discount = self.maximum_discount

        # Discount cannot exceed the total amount
        if discount > amount:
            discount = amount

        return discount

    def use_coupon(self) -> None:
        """Mark coupon as used (increment usage count)"""
        self.current_usage_count += 1
        self.updated_at = datetime.now(timezone.utc)

        # Auto-deactivate if usage limit reached
        if self.current_usage_count >= self.max_usage_count:
            self.status = CouponStatus.USED_UP


class Payment:
    """
    Payment domain entity
    Manages payment lifecycle and business rules
    """

    def __init__(
        self,
        payment_id: UUID,
        user_id: UUID,
        order_id: str,
        amount: Decimal,
        currency: str = "INR",
        subscription_type: SubscriptionType = None,
        status: PaymentStatus = PaymentStatus.CREATED,
        payment_method: Optional[PaymentMethod] = None,
        razorpay_payment_id: Optional[str] = None,
        razorpay_order_id: Optional[str] = None,
        razorpay_signature: Optional[str] = None,
        coupon_applied: Optional[UUID] = None,
        original_amount: Optional[Decimal] = None,
        discount_amount: Optional[Decimal] = None,
        receipt: Optional[str] = None,
        failure_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.payment_id = payment_id
        self.user_id = user_id
        self.order_id = order_id
        self.amount = amount
        self.currency = currency
        self.subscription_type = subscription_type
        self.status = status
        self.payment_method = payment_method
        self.razorpay_payment_id = razorpay_payment_id
        self.razorpay_order_id = razorpay_order_id
        self.razorpay_signature = razorpay_signature
        self.coupon_applied = coupon_applied
        self.original_amount = original_amount or amount
        self.discount_amount = discount_amount or Decimal("0")
        self.receipt = receipt
        self.failure_reason = failure_reason
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    @classmethod
    def create_for_subscription(
        cls,
        user_id: UUID,
        subscription_type: SubscriptionType,
        amount: Decimal,
        order_id: str,
        receipt: str = None,
    ) -> "Payment":
        """Create payment for subscription"""

        return cls(
            payment_id=uuid4(),
            user_id=user_id,
            order_id=order_id,
            amount=amount,
            subscription_type=subscription_type,
            receipt=receipt or f"sub_{subscription_type.value}_{user_id}",
            metadata={
                "subscription_type": subscription_type.value,
                "purpose": "subscription_purchase",
            },
        )

    def apply_coupon_discount(self, coupon: Coupon) -> None:
        """Apply coupon discount to payment"""

        # Validate coupon first
        is_valid, message = coupon.is_valid_for_amount(self.original_amount)
        if not is_valid:
            raise ValueError(f"Invalid coupon: {message}")

        # Calculate discount
        discount = coupon.calculate_discount(self.original_amount)

        # Apply discount
        self.discount_amount = discount
        self.amount = self.original_amount - discount
        self.coupon_applied = coupon.coupon_id
        self.updated_at = datetime.now(timezone.utc)

        # Add to metadata
        self.metadata.update(
            {
                "coupon_code": coupon.code,
                "coupon_type": coupon.coupon_type.value,
                "discount_applied": float(discount),
            }
        )

    def mark_as_authorized(self, razorpay_details: RazorpayPaymentDetails) -> None:
        """Mark payment as authorized"""
        self.status = PaymentStatus.AUTHORIZED
        self.razorpay_payment_id = razorpay_details.razorpay_payment_id
        self.razorpay_order_id = razorpay_details.razorpay_order_id
        self.razorpay_signature = razorpay_details.razorpay_signature
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_captured(self, payment_method: PaymentMethod = None) -> None:
        """Mark payment as successfully captured"""
        self.status = PaymentStatus.CAPTURED
        if payment_method:
            self.payment_method = payment_method
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_failed(self, reason: str) -> None:
        """Mark payment as failed"""
        self.status = PaymentStatus.FAILED
        self.failure_reason = reason
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_refunded(self) -> None:
        """Mark payment as refunded"""
        if self.status != PaymentStatus.CAPTURED:
            raise ValueError("Only captured payments can be refunded")

        self.status = PaymentStatus.REFUNDED
        self.updated_at = datetime.now(timezone.utc)

    def can_be_refunded(self) -> bool:
        """Check if payment can be refunded"""
        return self.status == PaymentStatus.CAPTURED

    def get_display_amount(self) -> str:
        """Get formatted amount for display"""
        return f"₹{self.amount:,.2f}"

    def get_discount_info(self) -> Optional[Dict[str, Any]]:
        """Get discount information if coupon was applied"""
        if not self.coupon_applied:
            return None

        return {
            "original_amount": float(self.original_amount),
            "discount_amount": float(self.discount_amount),
            "final_amount": float(self.amount),
            "coupon_code": self.metadata.get("coupon_code"),
            "savings": f"₹{self.discount_amount:,.2f}",
        }
