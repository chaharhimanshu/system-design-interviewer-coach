#!/usr/bin/env python3
"""
Test Session Flow
Test the session creation and memory persistence between start_interview and streaming
"""

import asyncio
import uuid
from app.application.services.ai_service import AIService
from app.domain.entities.session import (
    InterviewSession,
    SessionConfig,
    DifficultyLevel,
    SessionStatus,
)
from datetime import datetime


async def test_session_flow():
    """Test the complete session flow to debug memory persistence"""

    print("=== Testing Session Flow ===")

    # Create AIService instance (like the singleton)
    ai_service = AIService()

    # Create mock session data
    session_id = uuid.uuid4()
    print(f"Testing with session_id: {session_id}")

    # Create a mock session object
    session = InterviewSession(
        session_id=session_id,
        user_id=uuid.uuid4(),  # Mock user
        config=SessionConfig(
            topic="Design a URL Shortener",
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            max_duration_minutes=60,
            enable_hints=True,
            enable_real_time_feedback=True,
        ),
        status=SessionStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    print(f"Created mock session with topic: {session.config.topic}")

    try:
        # Step 1: Start interview (this should initialize memory)
        print("\n--- Step 1: Start Interview ---")
        start_result = await ai_service.start_interview_session(
            session=session, user_context={"experience_level": "intermediate"}
        )
        print(
            f"Start interview result: {start_result.get('question', 'No question generated')[:100]}..."
        )

        # Step 2: Try streaming chat (this should find the session in memory)
        print("\n--- Step 2: Stream Chat Response ---")
        user_message = (
            "I would use a load balancer, database sharding, and Redis for caching."
        )

        response_chunks = []
        async for chunk in ai_service.process_user_response_stream(
            session_id=session_id, user_message=user_message, message_type="answer"
        ):
            response_chunks.append(chunk)
            if chunk.get("type") == "content":
                print(f"Content chunk: {chunk.get('content', '')}", end="")
            elif chunk.get("type") == "status":
                print(f"\nStatus: {chunk.get('message')}")
            elif chunk.get("type") == "error":
                print(f"\nERROR: {chunk.get('message')}")
                break

        print(f"\nReceived {len(response_chunks)} total chunks")

        # Summary
        print("\n=== Test Summary ===")
        error_chunks = [c for c in response_chunks if c.get("type") == "error"]
        if error_chunks:
            print(f"❌ FAILED - {len(error_chunks)} error(s) occurred:")
            for error in error_chunks:
                print(f"   - {error.get('message')}")
        else:
            print("✅ SUCCESS - Session flow worked correctly!")

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_session_flow())
