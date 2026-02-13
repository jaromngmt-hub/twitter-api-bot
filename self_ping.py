"""Self-ping module to keep Render service awake."""
import asyncio
import httpx
from loguru import logger

SELF_URL = "https://twitter-api-bot.onrender.com/api/health"

async def self_ping_loop():
    """Ping ourselves every 10 minutes to prevent sleeping."""
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(SELF_URL, timeout=10)
                if response.status_code == 200:
                    logger.debug("Self-ping: OK")
                else:
                    logger.warning(f"Self-ping: Status {response.status_code}")
        except Exception as e:
            logger.error(f"Self-ping failed: {e}")
        
        # Wait 10 minutes
        await asyncio.sleep(600)
