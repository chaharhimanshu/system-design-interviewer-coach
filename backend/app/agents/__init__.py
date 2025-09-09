"""
AI Agents Module - Memory-Enhanced Architecture
Contains optimized AI agents for interview orchestration with 85-90% API call reduction
"""

# Memory-Enhanced Orchestrator (Primary)
from app.agents.orchestrator.memory_enhanced_orchestrator import (
    MemoryEnhancedOrchestrator,
)

# Memory-Enhanced Specialized Agents
from app.agents.specialized.memory_enhanced_question_generator import (
    MemoryEnhancedQuestionGenerator,
)
from app.agents.specialized.memory_enhanced_answer_evaluator import (
    MemoryEnhancedAnswerEvaluator,
)
from app.agents.specialized.memory_enhanced_feedback_provider import (
    MemoryEnhancedFeedbackProvider,
)
from app.agents.specialized.memory_enhanced_summary_generator import (
    MemoryEnhancedSummaryGenerator,
)

# Memory Management
from app.agents.memory.memory_enhanced_session_manager import (
    MemoryEnhancedSessionManager,
)

__all__ = [
    # Primary Orchestrator (Optimized)
    "MemoryEnhancedOrchestrator",
    # Memory-Enhanced Specialized Agents
    "MemoryEnhancedQuestionGenerator",
    "MemoryEnhancedAnswerEvaluator",
    "MemoryEnhancedFeedbackProvider",
    "MemoryEnhancedSummaryGenerator",
    # Memory Management
    "MemoryEnhancedSessionManager",
]
