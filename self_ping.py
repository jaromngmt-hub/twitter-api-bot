"""Self-ping to keep Render service awake."""
import asyncio
import httpx
from loguru import logger

async def self_ping():
    """Ping ourselves every 10 minutes to prevent sleeping."""
    url = "https://twitter-api-bot.onrender.com/api/health"
    while True:
        try:
            async with httpx.AsyncClient() as client:
                await client.get(url, timeout=10)
                logger.debug("Self-ping successful")
        except Exception as e:
            logger.error(f"Self-ping failed: {e}")
        await asyncio.sleep(600)  # 10 minutes
