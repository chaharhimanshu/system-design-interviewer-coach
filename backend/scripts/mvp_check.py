#!/usr/bin/env python
"""
MVP Readiness Check
Validates that all critical components are ready for MVP deployment
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def check_mvp_readiness():
    """Check MVP readiness status"""
    print("🚀 System Design Interview Coach - MVP Readiness Check")
    print("=" * 60)

    checks = {
        "database": False,
        "env_config": False,
        "api_endpoints": False,
        "ai_services": False,
        "task_queue": False,
        "websockets": False,
    }

    # 1. Database Check
    print("\n📊 Database & Schema Check")
    try:
        from app.infrastructure.database.config import DatabaseConfig

        db_config = DatabaseConfig()
        async with db_config.engine.connect() as conn:
            # Check if tables exist
            result = await conn.execute(
                """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'sessions', 'messages')
            """
            )
            tables = [row[0] for row in result.fetchall()]

            if len(tables) == 3:
                print("✅ Database connection & tables verified")
                checks["database"] = True
            else:
                print(f"❌ Missing tables. Found: {tables}")
                print("   Run: psql -d sdicoach -f scripts/init_db.sql")

        await db_config.engine.dispose()
    except Exception as e:
        print(f"❌ Database check failed: {e}")

    # 2. Environment Configuration
    print("\n⚙️  Environment Configuration Check")
    try:
        import os
        from dotenv import load_dotenv

        load_dotenv()

        critical_vars = [
            "DATABASE_URL",
            "OPENAI_API_KEY",
            "SECRET_KEY",
            "JWT_SECRET_KEY",
            "REDIS_URL",
        ]

        missing = [var for var in critical_vars if not os.getenv(var)]

        if not missing:
            print("✅ Critical environment variables configured")
            checks["env_config"] = True
        else:
            print(f"❌ Missing environment variables: {missing}")
            print("   Copy .env.example to .env and configure")
    except Exception as e:
        print(f"❌ Environment check failed: {e}")

    # 3. API Endpoints Check
    print("\n🌐 API Endpoints Check")
    try:
        from app.main import app

        routes = []
        for route in app.routes:
            if hasattr(route, "methods") and hasattr(route, "path"):
                routes.append(f"{list(route.methods)[0]} {route.path}")

        critical_endpoints = [
            "POST /api/v1/",  # Create session
            "GET /api/v1/",  # List sessions
            "POST /api/v1/auth/google",  # Auth
            "GET /api/v1/me",  # User profile
        ]

        # Check if critical endpoints exist (partial match)
        endpoint_exists = all(
            any(endpoint.split()[-1] in route for route in routes)
            for endpoint in critical_endpoints
        )

        if endpoint_exists:
            print("✅ Critical API endpoints available")
            checks["api_endpoints"] = True
        else:
            print("❌ Some critical endpoints missing")
    except Exception as e:
        print(f"❌ API endpoints check failed: {e}")

    # 4. AI Services Check
    print("\n🤖 AI Services Check")
    try:
        from app.application.services.ai_service import AIService
        from app.agents.orchestrator.main_orchestrator import InterviewOrchestrator

        # Just check if classes can be imported
        print("✅ AI service classes available")
        checks["ai_services"] = True
    except Exception as e:
        print(f"❌ AI services check failed: {e}")

    # 5. Task Queue Check
    print("\n⚡ Task Queue Check")
    try:
        from app.infrastructure.tasks.task_queue import TaskManager
        from app.infrastructure.tasks.task_processor import TaskProcessor

        print("✅ Task queue system available")
        checks["task_queue"] = True
    except Exception as e:
        print(f"❌ Task queue check failed: {e}")

    # 6. WebSocket Check
    print("\n🔌 WebSocket Check")
    try:
        from app.infrastructure.tasks.websocket_manager import ConnectionManager

        print("✅ WebSocket manager available")
        checks["websockets"] = True
    except Exception as e:
        print(f"❌ WebSocket check failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("🎯 MVP READINESS SUMMARY")
    print("=" * 60)

    passed = sum(checks.values())
    total = len(checks)

    for component, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {component.replace('_', ' ').title()}")

    print(f"\n📊 Status: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 MVP IS READY FOR DEPLOYMENT! 🎉")
        print("\nNext Steps:")
        print("1. Set up your .env file with actual API keys")
        print("2. Run database initialization: psql -d sdicoach -f scripts/init_db.sql")
        print("3. Start the server: python -m uvicorn app.main:app --reload")
        print("4. Test endpoints at: http://localhost:8000/docs")
        return True
    else:
        print(f"\n⚠️  MVP needs {total - passed} more components")
        print("\nCritical Issues to Fix:")

        for component, status in checks.items():
            if not status:
                if component == "database":
                    print(
                        "   • Run database setup: psql -d sdicoach -f scripts/init_db.sql"
                    )
                elif component == "env_config":
                    print("   • Copy .env.example to .env and configure API keys")
                else:
                    print(f"   • Fix {component.replace('_', ' ')}")

        return False


if __name__ == "__main__":
    success = asyncio.run(check_mvp_readiness())
    sys.exit(0 if success else 1)
