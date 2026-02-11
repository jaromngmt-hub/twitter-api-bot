"""Configuration management for Twitter Monitor Bot."""

import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # TwitterAPI.io
    TWITTERAPI_KEY: str = os.getenv("TWITTERAPI_KEY", "")
    
    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./monitor.db")
    
    # Monitoring
    CHECK_INTERVAL_SECONDS: int = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))
    MAX_TWEETS_PER_CHECK: int = int(os.getenv("MAX_TWEETS_PER_CHECK", "20"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Concurrency
    MAX_CONCURRENT_USERS: int = 10
    
    # Discord
    DISCORD_TIMEOUT: int = 10
    DISCORD_RETRY_ATTEMPTS: int = 3
    DISCORD_RETRY_DELAY: int = 1
    
    # TwitterAPI
    TWITTERAPI_BASE_URL: str = "https://api.twitterapi.io"
    TWITTERAPI_TIMEOUT: int = 30
    
    @classmethod
    def validate(cls) -> None:
        """Validate required settings."""
        if not cls.TWITTERAPI_KEY:
            logger.error("TWITTERAPI_KEY is not set in environment variables")
            raise ValueError("TWITTERAPI_KEY is required")
    
    @classmethod
    def ensure_data_dir(cls) -> None:
        """Ensure the data directory exists."""
        db_path = Path(cls.DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
