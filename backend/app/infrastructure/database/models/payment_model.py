"""
SQLAlchemy Payment Models
Database representation of Payment and Coupon entities
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    Text,
    Enum,
    JSON,
    ForeignKey,
    Index,
    DECIMAL,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base
from app.domain.entities.payment import (
    Payment,
    Coupon,
    PaymentStatus,
    PaymentMethod,
    SubscriptionType,
    CouponType,
    CouponStatus,
    RazorpayPaymentDetails,
)


class PaymentModel(Base):
    """SQLAlchemy Payment model"""

    __tablename__ = "payments"

    # Primary key
    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Payment details
    order_id = Column(String(255), nullable=False, unique=True, index=True)
    receipt = Column(String(255), nullable=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    original_amount = Column(DECIMAL(10, 2), nullable=True)
    discount_amount = Column(DECIMAL(10, 2), nullable=True, default=0)
    currency = Column(String(3), nullable=False, default="INR")

    # Subscription details
    subscription_type = Column(
        Enum(
            SubscriptionType,
            name="subscription_type",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
    )

    # Payment status and method
    status = Column(
        Enum(
            PaymentStatus,
            name="payment_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=PaymentStatus.CREATED,
    )

    payment_method = Column(
        Enum(
            PaymentMethod,
            name="payment_method",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
    )

    # Razorpay integration fields
    razorpay_payment_id = Column(String(255), nullable=True, unique=True, index=True)
    razorpay_order_id = Column(String(255), nullable=True, unique=True, index=True)
    razorpay_signature = Column(String(255), nullable=True)

    # Coupon information
    coupon_applied = Column(
        UUID(as_uuid=True), ForeignKey("coupons.coupon_id"), nullable=True
    )

    # Error handling
    failure_reason = Column(Text, nullable=True)

    # Additional metadata
    metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc)
    )
    authorized_at = Column(DateTime(timezone=True), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    coupon = relationship("CouponModel", back_populates="payments")

    # Indexes for performance
    __table_args__ = (
        Index("idx_payments_user_status", "user_id", "status"),
        Index("idx_payments_created_at", "created_at"),
        Index("idx_payments_subscription_type", "subscription_type"),
    )

    @classmethod
    def from_entity(cls, payment: Payment) -> "PaymentModel":
        """Convert Payment entity to PaymentModel"""
        model = cls(
            payment_id=payment.payment_id,
            user_id=payment.user_id,
            order_id=payment.order_id,
            receipt=payment.receipt,
            amount=payment.amount,
            original_amount=payment.original_amount,
            discount_amount=payment.discount_amount,
            currency=payment.currency,
            subscription_type=payment.subscription_type,
            status=payment.status,
            payment_method=payment.payment_method,
            razorpay_payment_id=(
                payment.razorpay_details.razorpay_payment_id
                if payment.razorpay_details
                else None
            ),
            razorpay_order_id=(
                payment.razorpay_details.razorpay_order_id
                if payment.razorpay_details
                else None
            ),
            razorpay_signature=(
                payment.razorpay_details.razorpay_signature
                if payment.razorpay_details
                else None
            ),
            coupon_applied=payment.coupon_applied,
            failure_reason=payment.failure_reason,
            metadata=payment.metadata,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            authorized_at=payment.authorized_at,
            captured_at=payment.captured_at,
        )
        return model

    def to_entity(self) -> Payment:
        """Convert PaymentModel to Payment entity"""
        # Create Razorpay details if they exist
        razorpay_details = None
        if (
            self.razorpay_payment_id
            and self.razorpay_order_id
            and self.razorpay_signature
        ):
            razorpay_details = RazorpayPaymentDetails(
                razorpay_payment_id=self.razorpay_payment_id,
                razorpay_order_id=self.razorpay_order_id,
                razorpay_signature=self.razorpay_signature,
            )

        payment = Payment(
            payment_id=self.payment_id,
            user_id=self.user_id,
            order_id=self.order_id,
            receipt=self.receipt,
            amount=self.amount,
            original_amount=self.original_amount,
            discount_amount=self.discount_amount,
            currency=self.currency,
            subscription_type=self.subscription_type,
            status=self.status,
            payment_method=self.payment_method,
            razorpay_details=razorpay_details,
            coupon_applied=self.coupon_applied,
            failure_reason=self.failure_reason,
            metadata=self.metadata,
            created_at=self.created_at,
            updated_at=self.updated_at,
            authorized_at=self.authorized_at,
            captured_at=self.captured_at,
        )
        return payment

    def update_from_entity(self, payment: Payment) -> None:
        """Update model fields from Payment entity"""
        self.amount = payment.amount
        self.original_amount = payment.original_amount
        self.discount_amount = payment.discount_amount
        self.subscription_type = payment.subscription_type
        self.status = payment.status
        self.payment_method = payment.payment_method

        # Update Razorpay details
        if payment.razorpay_details:
            self.razorpay_payment_id = payment.razorpay_details.razorpay_payment_id
            self.razorpay_order_id = payment.razorpay_details.razorpay_order_id
            self.razorpay_signature = payment.razorpay_details.razorpay_signature

        self.coupon_applied = payment.coupon_applied
        self.failure_reason = payment.failure_reason
        self.metadata = payment.metadata
        self.updated_at = payment.updated_at
        self.authorized_at = payment.authorized_at
        self.captured_at = payment.captured_at


class CouponModel(Base):
    """SQLAlchemy Coupon model"""

    __tablename__ = "coupons"

    # Primary key
    coupon_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Coupon identification
    code = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Coupon type and value
    coupon_type = Column(
        Enum(
            CouponType,
            name="coupon_type",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    discount_value = Column(DECIMAL(10, 2), nullable=False)

    # Usage constraints
    minimum_amount = Column(DECIMAL(10, 2), nullable=True)
    maximum_discount = Column(DECIMAL(10, 2), nullable=True)
    usage_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, nullable=False, default=0)

    # Validity period
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)

    # Status
    status = Column(
        Enum(
            CouponStatus,
            name="coupon_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=CouponStatus.ACTIVE,
    )

    # Metadata
    created_by = Column(String(255), nullable=True)
    metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc)
    )

    # Relationships
    payments = relationship("PaymentModel", back_populates="coupon")

    # Indexes for performance
    __table_args__ = (
        Index("idx_coupons_code_status", "code", "status"),
        Index("idx_coupons_valid_period", "valid_from", "valid_until"),
        Index("idx_coupons_status_usage", "status", "usage_limit", "used_count"),
    )

    @classmethod
    def from_entity(cls, coupon: Coupon) -> "CouponModel":
        """Convert Coupon entity to CouponModel"""
        model = cls(
            coupon_id=coupon.coupon_id,
            code=coupon.code,
            description=coupon.description,
            coupon_type=coupon.coupon_type,
            discount_value=coupon.discount_value,
            minimum_amount=coupon.minimum_amount,
            maximum_discount=coupon.maximum_discount,
            usage_limit=coupon.usage_limit,
            used_count=coupon.used_count,
            valid_from=coupon.valid_from,
            valid_until=coupon.valid_until,
            status=coupon.status,
            created_by=coupon.created_by,
            metadata=coupon.metadata,
            created_at=coupon.created_at,
            updated_at=coupon.updated_at,
        )
        return model

    def to_entity(self) -> Coupon:
        """Convert CouponModel to Coupon entity"""
        coupon = Coupon(
            coupon_id=self.coupon_id,
            code=self.code,
            description=self.description,
            coupon_type=self.coupon_type,
            discount_value=self.discount_value,
            minimum_amount=self.minimum_amount,
            maximum_discount=self.maximum_discount,
            usage_limit=self.usage_limit,
            used_count=self.used_count,
            valid_from=self.valid_from,
            valid_until=self.valid_until,
            status=self.status,
            created_by=self.created_by,
            metadata=self.metadata,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
        return coupon

    def update_from_entity(self, coupon: Coupon) -> None:
        """Update model fields from Coupon entity"""
        self.description = coupon.description
        self.coupon_type = coupon.coupon_type
        self.discount_value = coupon.discount_value
        self.minimum_amount = coupon.minimum_amount
        self.maximum_discount = coupon.maximum_discount
        self.usage_limit = coupon.usage_limit
        self.used_count = coupon.used_count
        self.valid_from = coupon.valid_from
        self.valid_until = coupon.valid_until
        self.status = coupon.status
        self.created_by = coupon.created_by
        self.metadata = coupon.metadata
        self.updated_at = coupon.updated_at
