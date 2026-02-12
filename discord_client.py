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
        return text[:self.MAX_TEXT_LENGTH - 3] + "..."
    
    def _format_tweet_text(self, tweet: Tweet) -> str:
        """Format tweet text with FULL content, handle RTs properly."""
        text = tweet.text
        
        # Handle retweets - extract and format properly
        if text.startswith("RT @"):
            # Format: "RT @username: original text"
            parts = text.split(": ", 1)
            if len(parts) == 2:
                rt_header = parts[0]  # "RT @username"
                original_text = parts[1]  # the actual tweet
                
                # Format as quote-style for clarity
                text = f"🔁 **{rt_header}**\n\n{original_text}"
        
        # Check length - Discord embed limit is 4096
        # If too long, truncate smartly with link to full tweet
        if len(text) > self.MAX_TEXT_LENGTH:
            # Truncate but keep more content
            truncated = text[:self.MAX_TEXT_LENGTH - 50]
            # Try to end at a word boundary
            last_space = truncated.rfind(" ")
            if last_space > self.MAX_TEXT_LENGTH - 100:
                truncated = truncated[:last_space]
            text = truncated + "\n\n... *(truncated - click link for full tweet)*"
        
        return text
    
    def _build_payload(self, username: str, tweet: Tweet, note: str = None) -> dict:
        """Build Discord webhook payload."""
        # Format text with full content
        description = self._format_tweet_text(tweet)
        
        # Add note if provided (e.g., "Built into project: xxx")
        if note:
            description = f"{note}\n\n{description}"
        
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
        
        return {
            "username": f"@{username}",
            "avatar_url": f"https://unavatar.io/twitter/{username}",
            "content": f"🔗 [View on Twitter]({tweet_url})",  # Direct link
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
            note: Optional note to add (e.g., "Built into project: xxx")
        
        Returns True if sent successfully, False otherwise.
        Raises DiscordWebhookError with 404 status for invalid webhooks.
        """
        payload = self._build_payload(username, tweet, note)
        
        for attempt in range(settings.DISCORD_RETRY_ATTEMPTS):
            try:
                response = await self.client.post(webhook_url, json=payload)
                
                if response.status_code == 204:
                    logger.debug(f"Successfully sent tweet {tweet.id} to Discord")
                    return True
                
                elif response.status_code == 404:
                    logger.error(f"Webhook not found (404): {webhook_url}")
                    raise DiscordWebhookError(f"Webhook not found (404)")
                
                elif 500 <= response.status_code < 600:
                    # Server error - retry
                    if attempt < settings.DISCORD_RETRY_ATTEMPTS - 1:
                        logger.warning(
                            f"Discord server error {response.status_code}, "
                            f"retrying in {settings.DISCORD_RETRY_DELAY}s..."
                        )
                        await asyncio.sleep(settings.DISCORD_RETRY_DELAY)
                        continue
                    else:
                        logger.error(
                            f"Discord server error after {settings.DISCORD_RETRY_ATTEMPTS} attempts: "
                            f"{response.status_code}"
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
