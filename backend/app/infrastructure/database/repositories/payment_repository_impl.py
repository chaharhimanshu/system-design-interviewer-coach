"""
Payment Repository Implementation - PostgreSQL with SQLAlchemy
Implements the payment and coupon repository interfaces for database operations
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.exc import IntegrityError

from app.domain.entities.payment import Payment, Coupon, PaymentStatus, CouponStatus
from app.domain.repositories.payment_repository import (
    IPaymentRepository,
    ICouponRepository,
)
from app.infrastructure.database.models.payment_model import PaymentModel, CouponModel
from app.shared.exceptions import DatabaseError, ResourceNotFoundError
from app.shared.logging import get_logger

logger = get_logger(__name__)


class PostgreSQLPaymentRepository(IPaymentRepository):
    """PostgreSQL implementation of payment repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payment: Payment) -> Payment:
        """Create a new payment"""
        try:
            payment_model = PaymentModel.from_entity(payment)
            self.session.add(payment_model)
            await self.session.commit()
            await self.session.refresh(payment_model)

            logger.info(f"Payment created: {payment.payment_id}")
            return payment_model.to_entity()

        except IntegrityError as e:
            await self.session.rollback()
            if "order_id" in str(e):
                raise DatabaseError("Payment with this order ID already exists")
            elif "razorpay_payment_id" in str(e):
                raise DatabaseError(
                    "Payment with this Razorpay payment ID already exists"
                )
            else:
                raise DatabaseError(f"Database integrity error: {str(e)}")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create payment: {str(e)}")
            raise DatabaseError(f"Failed to create payment: {str(e)}")

    async def get_by_id(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment by ID"""
        try:
            query = select(PaymentModel).where(PaymentModel.payment_id == payment_id)
            result = await self.session.execute(query)
            payment_model = result.scalar_one_or_none()

            if payment_model:
                return payment_model.to_entity()
            return None

        except Exception as e:
            logger.error(f"Failed to get payment by ID {payment_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve payment: {str(e)}")

    async def get_by_order_id(self, order_id: str) -> Optional[Payment]:
        """Get payment by Razorpay order ID"""
        try:
            query = select(PaymentModel).where(PaymentModel.order_id == order_id)
            result = await self.session.execute(query)
            payment_model = result.scalar_one_or_none()

            if payment_model:
                return payment_model.to_entity()
            return None

        except Exception as e:
            logger.error(f"Failed to get payment by order ID {order_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve payment: {str(e)}")

    async def get_by_razorpay_payment_id(
        self, razorpay_payment_id: str
    ) -> Optional[Payment]:
        """Get payment by Razorpay payment ID"""
        try:
            query = select(PaymentModel).where(
                PaymentModel.razorpay_payment_id == razorpay_payment_id
            )
            result = await self.session.execute(query)
            payment_model = result.scalar_one_or_none()

            if payment_model:
                return payment_model.to_entity()
            return None

        except Exception as e:
            logger.error(
                f"Failed to get payment by Razorpay payment ID {razorpay_payment_id}: {str(e)}"
            )
            raise DatabaseError(f"Failed to retrieve payment: {str(e)}")

    async def update(self, payment: Payment) -> Payment:
        """Update an existing payment"""
        try:
            # Find existing payment
            query = select(PaymentModel).where(
                PaymentModel.payment_id == payment.payment_id
            )
            result = await self.session.execute(query)
            payment_model = result.scalar_one_or_none()

            if not payment_model:
                raise ResourceNotFoundError(f"Payment not found: {payment.payment_id}")

            # Update model from entity
            payment_model.update_from_entity(payment)

            await self.session.commit()
            await self.session.refresh(payment_model)

            logger.info(f"Payment updated: {payment.payment_id}")
            return payment_model.to_entity()

        except ResourceNotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update payment {payment.payment_id}: {str(e)}")
            raise DatabaseError(f"Failed to update payment: {str(e)}")

    async def delete(self, payment_id: UUID) -> bool:
        """Delete a payment"""
        try:
            query = delete(PaymentModel).where(PaymentModel.payment_id == payment_id)
            result = await self.session.execute(query)
            await self.session.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Payment deleted: {payment_id}")
            return deleted

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete payment {payment_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete payment: {str(e)}")

    async def get_user_payments(
        self,
        user_id: UUID,
        status: Optional[PaymentStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Payment]:
        """Get payments for a user with optional filtering"""
        try:
            query = select(PaymentModel).where(PaymentModel.user_id == user_id)

            if status:
                query = query.where(PaymentModel.status == status)

            query = (
                query.order_by(desc(PaymentModel.created_at))
                .limit(limit)
                .offset(offset)
            )

            result = await self.session.execute(query)
            payment_models = result.scalars().all()

            return [model.to_entity() for model in payment_models]

        except Exception as e:
            logger.error(f"Failed to get user payments for {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve user payments: {str(e)}")

    async def get_successful_payments_by_user(self, user_id: UUID) -> List[Payment]:
        """Get all successful payments for a user"""
        try:
            query = (
                select(PaymentModel)
                .where(
                    and_(
                        PaymentModel.user_id == user_id,
                        PaymentModel.status == PaymentStatus.CAPTURED,
                    )
                )
                .order_by(desc(PaymentModel.captured_at))
            )

            result = await self.session.execute(query)
            payment_models = result.scalars().all()

            return [model.to_entity() for model in payment_models]

        except Exception as e:
            logger.error(
                f"Failed to get successful payments for user {user_id}: {str(e)}"
            )
            raise DatabaseError(f"Failed to retrieve successful payments: {str(e)}")

    async def get_pending_payments(self, older_than_minutes: int = 15) -> List[Payment]:
        """Get payments that are pending for too long"""
        try:
            cutoff_time = datetime.now(timezone.utc).timestamp() - (
                older_than_minutes * 60
            )
            cutoff_datetime = datetime.fromtimestamp(cutoff_time, tz=timezone.utc)

            query = (
                select(PaymentModel)
                .where(
                    and_(
                        PaymentModel.status.in_(
                            [PaymentStatus.CREATED, PaymentStatus.AUTHORIZED]
                        ),
                        PaymentModel.created_at < cutoff_datetime,
                    )
                )
                .order_by(PaymentModel.created_at)
            )

            result = await self.session.execute(query)
            payment_models = result.scalars().all()

            return [model.to_entity() for model in payment_models]

        except Exception as e:
            logger.error(f"Failed to get pending payments: {str(e)}")
            raise DatabaseError(f"Failed to retrieve pending payments: {str(e)}")


class PostgreSQLCouponRepository(ICouponRepository):
    """PostgreSQL implementation of coupon repository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, coupon: Coupon) -> Coupon:
        """Create a new coupon"""
        try:
            coupon_model = CouponModel.from_entity(coupon)
            self.session.add(coupon_model)
            await self.session.commit()
            await self.session.refresh(coupon_model)

            logger.info(f"Coupon created: {coupon.code}")
            return coupon_model.to_entity()

        except IntegrityError as e:
            await self.session.rollback()
            if "code" in str(e):
                raise DatabaseError("Coupon with this code already exists")
            else:
                raise DatabaseError(f"Database integrity error: {str(e)}")
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create coupon: {str(e)}")
            raise DatabaseError(f"Failed to create coupon: {str(e)}")

    async def get_by_id(self, coupon_id: UUID) -> Optional[Coupon]:
        """Get coupon by ID"""
        try:
            query = select(CouponModel).where(CouponModel.coupon_id == coupon_id)
            result = await self.session.execute(query)
            coupon_model = result.scalar_one_or_none()

            if coupon_model:
                return coupon_model.to_entity()
            return None

        except Exception as e:
            logger.error(f"Failed to get coupon by ID {coupon_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve coupon: {str(e)}")

    async def get_by_code(self, code: str) -> Optional[Coupon]:
        """Get coupon by code"""
        try:
            query = select(CouponModel).where(CouponModel.code == code.upper())
            result = await self.session.execute(query)
            coupon_model = result.scalar_one_or_none()

            if coupon_model:
                return coupon_model.to_entity()
            return None

        except Exception as e:
            logger.error(f"Failed to get coupon by code {code}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve coupon: {str(e)}")

    async def update(self, coupon: Coupon) -> Coupon:
        """Update an existing coupon"""
        try:
            # Find existing coupon
            query = select(CouponModel).where(CouponModel.coupon_id == coupon.coupon_id)
            result = await self.session.execute(query)
            coupon_model = result.scalar_one_or_none()

            if not coupon_model:
                raise ResourceNotFoundError(f"Coupon not found: {coupon.coupon_id}")

            # Update model from entity
            coupon_model.update_from_entity(coupon)

            await self.session.commit()
            await self.session.refresh(coupon_model)

            logger.info(f"Coupon updated: {coupon.code}")
            return coupon_model.to_entity()

        except ResourceNotFoundError:
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update coupon {coupon.coupon_id}: {str(e)}")
            raise DatabaseError(f"Failed to update coupon: {str(e)}")

    async def delete(self, coupon_id: UUID) -> bool:
        """Delete a coupon"""
        try:
            query = delete(CouponModel).where(CouponModel.coupon_id == coupon_id)
            result = await self.session.execute(query)
            await self.session.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Coupon deleted: {coupon_id}")
            return deleted

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete coupon {coupon_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete coupon: {str(e)}")

    async def get_active_coupons(self) -> List[Coupon]:
        """Get all active coupons"""
        try:
            current_time = datetime.now(timezone.utc)

            query = (
                select(CouponModel)
                .where(
                    and_(
                        CouponModel.status == CouponStatus.ACTIVE,
                        CouponModel.valid_from <= current_time,
                        CouponModel.valid_until >= current_time,
                        or_(
                            CouponModel.usage_limit.is_(None),
                            CouponModel.used_count < CouponModel.usage_limit,
                        ),
                    )
                )
                .order_by(CouponModel.created_at)
            )

            result = await self.session.execute(query)
            coupon_models = result.scalars().all()

            return [model.to_entity() for model in coupon_models]

        except Exception as e:
            logger.error(f"Failed to get active coupons: {str(e)}")
            raise DatabaseError(f"Failed to retrieve active coupons: {str(e)}")

    async def get_coupons_by_status(self, status: CouponStatus) -> List[Coupon]:
        """Get coupons by status"""
        try:
            query = (
                select(CouponModel)
                .where(CouponModel.status == status)
                .order_by(CouponModel.created_at)
            )

            result = await self.session.execute(query)
            coupon_models = result.scalars().all()

            return [model.to_entity() for model in coupon_models]

        except Exception as e:
            logger.error(f"Failed to get coupons by status {status}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve coupons by status: {str(e)}")

    async def get_expired_coupons(self) -> List[Coupon]:
        """Get expired coupons that need cleanup"""
        try:
            current_time = datetime.now(timezone.utc)

            query = (
                select(CouponModel)
                .where(
                    and_(
                        CouponModel.status == CouponStatus.ACTIVE,
                        CouponModel.valid_until < current_time,
                    )
                )
                .order_by(CouponModel.valid_until)
            )

            result = await self.session.execute(query)
            coupon_models = result.scalars().all()

            return [model.to_entity() for model in coupon_models]

        except Exception as e:
            logger.error(f"Failed to get expired coupons: {str(e)}")
            raise DatabaseError(f"Failed to retrieve expired coupons: {str(e)}")

    async def increment_usage_count(self, coupon_id: UUID) -> bool:
        """Increment coupon usage count atomically"""
        try:
            query = (
                update(CouponModel)
                .where(CouponModel.coupon_id == coupon_id)
                .values(
                    used_count=CouponModel.used_count + 1,
                    updated_at=datetime.now(timezone.utc),
                )
            )

            result = await self.session.execute(query)
            await self.session.commit()

            updated = result.rowcount > 0
            if updated:
                logger.info(f"Coupon usage count incremented: {coupon_id}")
            return updated

        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"Failed to increment coupon usage count {coupon_id}: {str(e)}"
            )
            raise DatabaseError(f"Failed to increment coupon usage count: {str(e)}")

    async def get_usage_count(self, coupon_id: UUID) -> int:
        """Get current usage count for a coupon"""
        try:
            query = select(CouponModel.used_count).where(
                CouponModel.coupon_id == coupon_id
            )
            result = await self.session.execute(query)
            usage_count = result.scalar_one_or_none()

            return usage_count if usage_count is not None else 0

        except Exception as e:
            logger.error(f"Failed to get coupon usage count {coupon_id}: {str(e)}")
            raise DatabaseError(f"Failed to get coupon usage count: {str(e)}")
