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
    
    # OpenAI (for tweet analysis)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
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
    
    # Tiered Discord Webhooks (for AI rating system)
    # Tier 2 (4-6 score): Standard updates
    DISCORD_WEBHOOK_TIER2: str = os.getenv("DISCORD_WEBHOOK_TIER2", "")
    # Tier 3 (7-8 score): Premium alpha
    DISCORD_WEBHOOK_TIER3: str = os.getenv("DISCORD_WEBHOOK_TIER3", "")
    # Tier 4 (9-10 score): Urgent alerts
    DISCORD_WEBHOOK_TIER4: str = os.getenv("DISCORD_WEBHOOK_TIER4", "")
    
    # AI Analysis Settings
    ENABLE_AI_ANALYSIS: bool = os.getenv("ENABLE_AI_ANALYSIS", "true").lower() == "true"
    AI_MIN_SCORE_TO_SEND: int = int(os.getenv("AI_MIN_SCORE_TO_SEND", "4"))  # Filter < 4
    
    # Urgent Notifications (Score 9-10 to phone)
    URGENT_NOTIFICATIONS_ENABLED: bool = os.getenv("URGENT_NOTIFICATIONS_ENABLED", "false").lower() == "true"
    URGENT_MIN_SCORE: int = int(os.getenv("URGENT_MIN_SCORE", "9"))  # Only 9-10 scores
    
    # Twilio (SMS/WhatsApp)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")  # Twilio number
    YOUR_PHONE_NUMBER: str = os.getenv("YOUR_PHONE_NUMBER", "")  # Your real number
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Pushover
    PUSHOVER_APP_TOKEN: str = os.getenv("PUSHOVER_APP_TOKEN", "")
    PUSHOVER_USER_KEY: str = os.getenv("PUSHOVER_USER_KEY", "")
    
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
