"""
Payment Repository Interfaces
Domain layer contracts for payment persistence
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.domain.entities.payment import Payment, Coupon


class IPaymentRepository(ABC):
    """Payment repository interface"""

    @abstractmethod
    async def create(self, payment: Payment) -> Payment:
        """Create a new payment record"""
        pass

    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> Optional[Payment]:
        """Get payment by ID"""
        pass

    @abstractmethod
    async def get_by_order_id(self, order_id: str) -> Optional[Payment]:
        """Get payment by Razorpay order ID"""
        pass

    @abstractmethod
    async def get_by_razorpay_payment_id(
        self, razorpay_payment_id: str
    ) -> Optional[Payment]:
        """Get payment by Razorpay payment ID"""
        pass

    @abstractmethod
    async def get_user_payments(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[Payment]:
        """Get user's payment history"""
        pass

    @abstractmethod
    async def update(self, payment: Payment) -> Payment:
        """Update payment record"""
        pass

    @abstractmethod
    async def delete(self, payment_id: UUID) -> bool:
        """Delete payment record"""
        pass


class ICouponRepository(ABC):
    """Coupon repository interface"""

    @abstractmethod
    async def create(self, coupon: Coupon) -> Coupon:
        """Create a new coupon"""
        pass

    @abstractmethod
    async def get_by_id(self, coupon_id: UUID) -> Optional[Coupon]:
        """Get coupon by ID"""
        pass

    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Coupon]:
        """Get coupon by code"""
        pass

    @abstractmethod
    async def get_active_coupons(self) -> List[Coupon]:
        """Get all active coupons"""
        pass

    @abstractmethod
    async def update(self, coupon: Coupon) -> Coupon:
        """Update coupon"""
        pass

    @abstractmethod
    async def delete(self, coupon_id: UUID) -> bool:
        """Delete coupon"""
        pass
