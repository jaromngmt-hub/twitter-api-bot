"""Discord webhook client for sending tweets."""

import asyncio
from datetime import datetime
from typing import Optional

import httpx
from loguru import logger

from config import settings
from models import Tweet


class DiscordWebhookError(Exception):
    """Discord webhook error."""
    pass


class DiscordClient:
    """Async client for Discord webhooks."""
    
    MAX_TEXT_LENGTH = 3900  # Discord limit is 4096, leave room for formatting
    AVATAR_URL = "https://abs.twimg.com/icons/apple-touch-icon-192x192.png"
    BOT_USERNAME = "Twitter Monitor"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.DISCORD_TIMEOUT),
            headers={"Content-Type": "application/json"}
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _format_metrics(self, tweet: Tweet) -> str:
        """Format tweet metrics for Discord footer."""
        # Format numbers (e.g., 1200 -> 1.2k)
        def format_number(n: int) -> str:
            if n >= 1000000:
                return f"{n/1000000:.1f}M"
            elif n >= 1000:
                return f"{n/1000:.1f}k"
            return str(n)
        
        likes = format_number(tweet.likes)
        retweets = format_number(tweet.retweets)
        replies = format_number(tweet.replies)
        
        return f"❤️ {likes} | 🔁 {retweets} | 💬 {replies}"
    
    def _format_timestamp(self, dt: datetime) -> str:
        """Format datetime for Discord timestamp."""
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    
    def _truncate_text(self, text: str) -> str:
        """Truncate text to Discord's limit."""
        if len(text) <= self.MAX_TEXT_LENGTH:
            return text
        return text[:self.MAX_TEXT_LENGTH-3] + "..."
    
    def _build_payload(self, username: str, tweet: Tweet, note: str = None) -> dict:
        """Build Discord webhook payload."""
        # Truncate description
        description = self._truncate_text(tweet.text)
        
        # Get first media URL if available
        image_url = tweet.media_urls[0] if tweet.media_urls else None
        
        # Build tweet URL
        tweet_url = f"https://twitter.com/{username}/status/{tweet.id}"
        
        embed = {
            "description": description,
            "color": 1942002,  # Twitter blue
            "timestamp": self._format_timestamp(tweet.created_at),
            "footer": {
                "text": f"@{username} | {self._format_metrics(tweet)}"
            },
            "url": tweet_url  # Clicking embed goes to tweet
        }
        
        # Add image if exists
        if image_url:
            embed["image"] = {"url": image_url}
        
        content = f"🔗 [View on Twitter]({tweet_url})"
        if note:
            content = f"{note}\n{content}"
        
        return {
            "username": f"@{username}",
            "avatar_url": f"https://unavatar.io/twitter/{username}",
            "content": content,
            "embeds": [embed]
        }
    
    async def send_tweet(
        self,
        webhook_url: str,
        username: str,
        tweet: Tweet,
        note: str = None
    ) -> bool:
        """
        Send a tweet to Discord webhook.
        
        Args:
            note: Optional note to add (e.g. "Built into project: xxx")
        
        Returns True if sent successfully, False otherwise.
        Raises DiscordWebhookError with 404 status for invalid webhooks.
        """
        payload = self._build_payload(username, tweet, note)
        
        for attempt in range(settings.DISCORD_RETRY_ATTEMPTS):
            try:
                response = await self.client.post(webhook_url, json=payload)
                
                if response.status_code == 204:
                    logger.info(f"Discord notification sent for @{username}")
                    return True
                
                elif response.status_code == 404:
                    # Webhook doesn't exist - raise specific error
                    raise DiscordWebhookError(
                        f"Discord webhook returned 404 - webhook may have been deleted. "
                        f"URL: {webhook_url[:50]}..."
                    )
                
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 5))
                    logger.warning(f"Discord rate limited, waiting {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    continue
                
                elif 500 <= response.status_code < 600:
                    # Server error, retry
                    if attempt < settings.DISCORD_RETRY_ATTEMPTS - 1:
                        logger.warning(
                            f"Discord server error {response.status_code}, retrying..."
                        )
                        await asyncio.sleep(settings.DISCORD_RETRY_DELAY)
                        continue
                    else:
                        logger.error(
                            f"Discord server error {response.status_code} after all retries"
                        )
                        return False
                
                else:
                    logger.error(
                        f"Discord webhook error {response.status_code}: {response.text}"
                    )
                    return False
            
            except httpx.TimeoutException:
                if attempt < settings.DISCORD_RETRY_ATTEMPTS - 1:
                    logger.warning(f"Discord timeout, retrying...")
                    await asyncio.sleep(settings.DISCORD_RETRY_DELAY)
                    continue
                logger.error("Discord webhook timeout after all retries")
                return False
            
            except httpx.RequestError as e:
                if attempt < settings.DISCORD_RETRY_ATTEMPTS - 1:
                    logger.warning(f"Discord request error: {e}, retrying...")
                    await asyncio.sleep(settings.DISCORD_RETRY_DELAY)
                    continue
                logger.error(f"Discord request error after all retries: {e}")
                return False
        
        return False
    
    async def send_interesting(
        self,
        username: str,
        tweet_text: str,
        score: int,
        reason: str = "User marked as INTERESTING"
    ) -> bool:
        """Send an 'interesting' tweet to Discord."""
        from datetime import datetime
        
        webhook_url = settings.DISCORD_WEBHOOK_INTERESTING
        if not webhook_url:
            logger.warning("No INTERESTING webhook configured")
            return False
        
        # Create a minimal Tweet-like object
        class FakeTweet:
            def __init__(self, text):
                self.text = text
                self.id = "unknown"
                self.created_at = datetime.now()
                self.likes = 0
                self.retweets = 0
                self.replies = 0
                self.media_urls = []
        
        fake_tweet = FakeTweet(tweet_text)
        
        payload = {
            "username": "Twitter Monitor",
            "avatar_url": self.AVATAR_URL,
            "content": f"📌 INTERESTING from Telegram | Score: {score}/10",
            "embeds": [{
                "description": tweet_text[:3900],
                "color": 3447003,  # Blue
                "footer": {"text": f"@{username} | {reason}"}
            }]
        }
        
        try:
            response = await self.client.post(webhook_url, json=payload)
            return response.status_code == 204
        except Exception as e:
            logger.error(f"Failed to send to INTERESTING channel: {e}")
            return False


# Global instance
discord_client = DiscordClient()
