"""
Test script to verify interview limit enforcement
"""

import asyncio
from datetime import datetime, timedelta
from uuid import UUID, uuid4


# Mock implementations for testing
class MockUser:
    def __init__(self, user_id, subscription_type="free", subscription_expiry=None):
        self.user_id = user_id
        self.subscription_type = subscription_type
        self.subscription_expiry = subscription_expiry
        self.interviews_this_month = 0
        self.total_interviews = 0


class MockUserService:
    def __init__(self):
        self.users = {}

    async def check_interview_creation_limits(self, user_id):
        user = self.users.get(user_id)
        if not user:
            return False, "User not found"

        # Check subscription status
        if user.subscription_type in ["lifetime", "premium"]:
            return True, "Premium user - unlimited interviews"

        if user.subscription_type == "monthly":
            if user.subscription_expiry and user.subscription_expiry > datetime.now():
                return True, "Active monthly subscription - unlimited interviews"

        # Free user - check monthly limit
        if user.interviews_this_month >= 2:
            return (
                False,
                "Free users can only create 2 interviews per month. Upgrade to premium for unlimited interviews.",
            )

        return (
            True,
            f"Free user - {2 - user.interviews_this_month} interviews remaining this month",
        )

    async def record_interview_creation(self, user_id):
        user = self.users.get(user_id)
        if user:
            user.interviews_this_month += 1
            user.total_interviews += 1


async def test_interview_limits():
    service = MockUserService()

    # Test Case 1: Free user with no interviews
    free_user_id = uuid4()
    service.users[free_user_id] = MockUser(free_user_id, "free")

    print("=== Test Case 1: Free user - First interview ===")
    can_create, reason = await service.check_interview_creation_limits(free_user_id)
    print(f"Can create: {can_create}, Reason: {reason}")

    if can_create:
        await service.record_interview_creation(free_user_id)
        print(
            f"Interviews this month: {service.users[free_user_id].interviews_this_month}"
        )

    # Test Case 2: Free user - Second interview
    print("\n=== Test Case 2: Free user - Second interview ===")
    can_create, reason = await service.check_interview_creation_limits(free_user_id)
    print(f"Can create: {can_create}, Reason: {reason}")

    if can_create:
        await service.record_interview_creation(free_user_id)
        print(
            f"Interviews this month: {service.users[free_user_id].interviews_this_month}"
        )

    # Test Case 3: Free user - Third interview (should be blocked)
    print("\n=== Test Case 3: Free user - Third interview (should be blocked) ===")
    can_create, reason = await service.check_interview_creation_limits(free_user_id)
    print(f"Can create: {can_create}, Reason: {reason}")

    # Test Case 4: Premium user - unlimited
    premium_user_id = uuid4()
    service.users[premium_user_id] = MockUser(premium_user_id, "lifetime")

    print("\n=== Test Case 4: Premium user - unlimited interviews ===")
    can_create, reason = await service.check_interview_creation_limits(premium_user_id)
    print(f"Can create: {can_create}, Reason: {reason}")

    # Test Case 5: Monthly subscriber with active subscription
    monthly_user_id = uuid4()
    service.users[monthly_user_id] = MockUser(
        monthly_user_id, "monthly", datetime.now() + timedelta(days=15)
    )

    print("\n=== Test Case 5: Monthly subscriber - active subscription ===")
    can_create, reason = await service.check_interview_creation_limits(monthly_user_id)
    print(f"Can create: {can_create}, Reason: {reason}")


if __name__ == "__main__":
    asyncio.run(test_interview_limits())
