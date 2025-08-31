"""
FastAPI Application Entry Point
System Design Interview Coach - User Service MVP
"""

import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Setup logging first
from app.shared.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# Import infrastructure
from app.infrastructure.database.config import db_config

# Import API routes
from app.interfaces.api.v1.user_endpoints import router as user_router
from app.interfaces.api.v1.async_session_endpoints import router as async_session_router
from app.interfaces.api.v1.websocket_endpoints import router as websocket_router

# Import exceptions
from app.shared.exceptions import SDCoachException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting System Design Interview Coach API")

    try:
        # Verify database connection
        async with db_config.engine.connect() as conn:
            await conn.execute("SELECT 1")
        logger.info("Database connection verified successfully")

        # Note: Database schema should be managed via SQL scripts
        # Run your SQL migration scripts before starting the application

        # Initialize task infrastructure
        from app.infrastructure.tasks.task_queue import get_task_manager
        from app.infrastructure.tasks.task_processor import start_task_processor

        # Initialize task manager
        await get_task_manager()
        logger.info("Task manager initialized successfully")

        # Start background task processor
        await start_task_processor()
        logger.info("Background task processor started successfully")

    except Exception as e:
        logger.error(f"Failed to start application components: {str(e)}", exc_info=True)
        raise

    yield

    logger.info("Shutting down System Design Interview Coach API")

    # Cleanup task infrastructure
    try:
        from app.infrastructure.tasks.task_processor import stop_task_processor
        from app.infrastructure.tasks.task_queue import cleanup_task_manager

        await stop_task_processor()
        await cleanup_task_manager()
        logger.info("Task infrastructure cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title="System Design Interview Coach",
        description="AI-powered system design interview practice platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler for custom exceptions
    @app.exception_handler(SDCoachException)
    async def custom_exception_handler(request: Request, exc: SDCoachException):
        logger.warning(
            f"Custom exception: {exc.message}",
            extra={"error_code": exc.error_code, "endpoint": str(request.url)},
        )
        return JSONResponse(
            status_code=400,
            content={"error": exc.message, "error_code": exc.error_code},
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        logger.info("Health check endpoint called")
        return {"status": "healthy", "service": "sdcoach-api", "version": "1.0.0"}

    # Root endpoint
    @app.get("/")
    async def root():
        logger.info("Root endpoint called")
        return {
            "name": "System Design Interview Coach",
            "version": "1.0.0",
            "docs": "/docs",
            "status": "healthy",
        }

    # Include user router with API prefix
    app.include_router(user_router, prefix="/api/v1")

    # Include async session router with API prefix (new asynchronous endpoints)
    app.include_router(async_session_router, prefix="/api/v1")

    # Include WebSocket router
    app.include_router(websocket_router, prefix="/api/v1")

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("RELOAD", "true").lower() == "true",
        workers=int(os.getenv("WORKERS", 1)),
    )
