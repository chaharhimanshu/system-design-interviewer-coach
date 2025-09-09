#!/usr/bin/env python3
"""
Memory Debug Script
Quick script to inspect LangGraph memory contents for debugging
"""

import asyncio
import json
from app.agents.orchestrator.memory_enhanced_orchestrator import (
    MemoryEnhancedOrchestrator,
)


async def debug_session_memory(session_id: str):
    """Debug a specific session's memory contents"""
    print(f"\n🔍 Debugging memory for session: {session_id}")
    print("=" * 60)

    orchestrator = MemoryEnhancedOrchestrator()

    # Debug memory contents
    debug_info = await orchestrator.debug_memory_contents(session_id)

    print(json.dumps(debug_info, indent=2, default=str))

    return debug_info


async def debug_all_memory():
    """Debug all memory threads"""
    print("\n🔍 Debugging all memory threads")
    print("=" * 60)

    orchestrator = MemoryEnhancedOrchestrator()

    # Debug all memory
    all_memory = await orchestrator.debug_all_memory_threads()

    print(json.dumps(all_memory, indent=2, default=str))

    return all_memory


async def main():
    """Main debug function"""
    print("🧠 LangGraph Memory Debug Tool")
    print("=" * 60)

    # First, show all memory threads
    await debug_all_memory()

    # Ask user for specific session to debug
    session_id = input(
        "\n📝 Enter session ID to debug (or press Enter to skip): "
    ).strip()

    if session_id:
        await debug_session_memory(session_id)

    print("\n✅ Memory debugging complete!")


if __name__ == "__main__":
    asyncio.run(main())
