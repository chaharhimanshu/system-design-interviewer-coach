"""
Application Configuration Settings
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""

    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore")

    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="system_design_coach", env="DB_NAME")
    user: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="password", env="DB_PASSWORD")

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis configuration settings"""

    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")

    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class OpenAISettings(BaseSettings):
    """OpenAI API configuration settings"""

    model_config = SettingsConfigDict(env_prefix="OPENAI_", extra="ignore")

    api_key: str = Field(..., env="OPENAI_API_KEY")
    model: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")

    # Agent-specific settings
    evaluation_temperature: float = Field(
        default=0.3, env="OPENAI_EVALUATION_TEMPERATURE"
    )
    feedback_temperature: float = Field(default=0.6, env="OPENAI_FEEDBACK_TEMPERATURE")
    question_temperature: float = Field(default=0.8, env="OPENAI_QUESTION_TEMPERATURE")


class APISettings(BaseSettings):
    """API configuration settings"""

    model_config = SettingsConfigDict(env_prefix="API_", extra="ignore")

    title: str = "System Design Interview Coach API"
    version: str = "1.0.0"
    description: str = "API for AI-powered system design interview coaching"

    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"], env="CORS_ORIGINS"
    )


class SessionSettings(BaseSettings):
    """Session management settings"""

    model_config = SettingsConfigDict(env_prefix="SESSION_", extra="ignore")

    default_timeout_minutes: int = Field(default=60, env="SESSION_TIMEOUT_MINUTES")
    max_sessions_per_user: int = Field(default=5, env="MAX_SESSIONS_PER_USER")
    cleanup_interval_minutes: int = Field(default=30, env="SESSION_CLEANUP_INTERVAL")


class AISettings(BaseSettings):
    """AI service configuration settings"""

    model_config = SettingsConfigDict(env_prefix="AI_", extra="ignore")

    memory_sliding_window: int = Field(default=20, env="AI_MEMORY_WINDOW")
    max_conversation_length: int = Field(default=100, env="AI_MAX_CONVERSATION_LENGTH")

    # Performance tracking settings
    performance_window_size: int = Field(default=5, env="AI_PERFORMANCE_WINDOW")
    difficulty_adjustment_threshold: float = Field(
        default=0.3, env="AI_DIFFICULTY_THRESHOLD"
    )

    # Response timeouts
    openai_timeout_seconds: int = Field(default=30, env="AI_OPENAI_TIMEOUT")


class SSESettings(BaseSettings):
    """Server-Sent Events configuration settings"""

    model_config = SettingsConfigDict(env_prefix="SSE_", extra="ignore")

    heartbeat_interval: int = Field(default=30, env="SSE_HEARTBEAT_INTERVAL")
    connection_timeout: int = Field(default=300, env="SSE_CONNECTION_TIMEOUT")
    retry_timeout: int = Field(default=3000, env="SSE_RETRY_TIMEOUT")
    max_connections_per_session: int = Field(
        default=5, env="SSE_MAX_CONNECTIONS_PER_SESSION"
    )
    cleanup_interval: int = Field(default=60, env="SSE_CLEANUP_INTERVAL")


class Settings(BaseSettings):
    """Main application settings"""

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")

    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    openai: OpenAISettings = OpenAISettings()
    api: APISettings = APISettings()
    session: SessionSettings = SessionSettings()
    ai: AISettings = AISettings()
    sse: SSESettings = SSESettings()

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT"
    )

    @property
    def redis_url(self) -> str:
        """Get Redis URL for connections"""
        return self.redis.url


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
