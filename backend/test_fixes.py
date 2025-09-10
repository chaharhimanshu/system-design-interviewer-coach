#!/usr/bin/env python3
"""
Test the fixes for conversation messages and overall_score issues
"""

import asyncio
import uuid
from app.agents.memory.memory_enhanced_session_manager import (
    MemoryEnhancedSessionManager,
)
from app.agents.models.output_schemas import (
    AnswerEvaluation,
    EvaluationScores,
    AnswerAnalysis,
    NextSteps,
)
from datetime import datetime


async def test_conversation_messages():
    """Test that conversation messages can be stored and retrieved"""
    print("=== Testing Conversation Messages ===")

    session_manager = MemoryEnhancedSessionManager()
    session_id = str(uuid.uuid4())

    try:
        # Test 1: Add a message
        print(f"1. Adding message to session {session_id}")
        await session_manager.add_message_to_memory(
            session_id=session_id,
            role="USER",
            content="Hello, this is a test message",
            message_type="TEXT",
        )
        print("✅ Message added successfully")

        # Test 2: Retrieve messages
        print("2. Retrieving conversation messages")
        messages = await session_manager.get_conversation_messages(session_id)
        print(f"✅ Retrieved {len(messages)} messages")

        if len(messages) > 0:
            print(f"   First message: {messages[0].content[:50]}...")
        else:
            print(
                "   No messages found (this might be expected if database is not set up)"
            )

    except Exception as e:
        print(f"❌ Error: {e}")


def test_overall_score():
    """Test that overall_score is correctly accessed"""
    print("\n=== Testing Overall Score Access ===")

    try:
        # Create a sample AnswerEvaluation
        scores = EvaluationScores(
            clarity=8.5,
            technical_depth=7.0,
            scalability_awareness=6.5,
            trade_offs_understanding=7.5,
        )

        analysis = AnswerAnalysis(
            strengths=["Good explanation"],
            weaknesses=["Could be more detailed"],
            missing_topics=["Performance considerations"],
            technical_errors=[],
        )

        next_steps = NextSteps(
            needs_clarification=False,
            needs_deeper_dive=True,
            ready_for_next_topic=False,
            suggested_follow_up="deeper_dive",
            specific_areas_to_explore=["scalability"],
        )

        evaluation = AnswerEvaluation(
            scores=scores,
            analysis=analysis,
            next_steps=next_steps,
            evaluation_timestamp=datetime.now(),
            confidence_level=0.85,
        )

        # Test accessing the average score (this is what orchestrator should use)
        average_score = evaluation.scores.average_score
        print(f"✅ Average score calculated: {average_score}")
        print(
            f"   Individual scores: clarity={scores.clarity}, technical_depth={scores.technical_depth}"
        )
        print(
            f"   scalability_awareness={scores.scalability_awareness}, trade_offs={scores.trade_offs_understanding}"
        )

        # Test that trying to access overall_score fails (as expected)
        try:
            overall_score = evaluation.overall_score
            print(f"❌ Unexpected: overall_score exists: {overall_score}")
        except AttributeError:
            print("✅ Correctly - overall_score attribute does not exist")

    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all tests"""
    print("🧪 Testing Agent Fixes")
    print("=" * 50)

    await test_conversation_messages()
    test_overall_score()

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
