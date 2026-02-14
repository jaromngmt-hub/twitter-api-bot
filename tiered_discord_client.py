"""Tiered Discord webhook client for routing tweets by importance."""

import asyncio
from datetime import datetime
from typing import Optional

import httpx
from loguru import logger

from config import settings
from models import Tweet


class TieredDiscordClient:
    """
    Routes tweets to different Discord channels based on AI rating.
    
    Tier System:
    - Tier 1 (Score 1-3): Filtered out (low value)
    - Tier 2 (Score 4-6): Standard channel (general updates)
    - Tier 3 (Score 7-8): Premium channel (high value alpha)
    - Tier 4 (Score 9-10): Urgent channel (critical alpha)
    """
    
    MAX_TEXT_LENGTH = 4096
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10),
            headers={"Content-Type": "application/json"}
        )
        
        # Load tier webhooks from config
        self.tier_webhooks = {
            1: None,  # Filtered - no webhook
            2: settings.DISCORD_WEBHOOK_TIER2,  # Standard
            3: settings.DISCORD_WEBHOOK_TIER3,  # Premium
            4: settings.DISCORD_WEBHOOK_TIER4,  # Urgent
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def get_tier_from_score(self, score: int) -> int:
        """Convert score (1-10) to tier (1-4)."""
        if score <= 3:
            return 1  # Filter
        elif score <= 6:
            return 2  # Standard
        elif score <= 8:
            return 3  # Premium
        else:
            return 4  # Urgent
    
    async def send_tweet(self, username: str, tweet: Tweet, rating: dict) -> dict:
        """
        Send tweet to appropriate tier channel.
        
        Returns:
            {"sent": bool, "tier": int, "webhook": str, "error": str|None}
        """
        score = rating.get("score", 5)
        tier = self.get_tier_from_score(score)
        
        # Tier 1 = filtered out
        if tier == 1:
            logger.info(f"Tweet from @{username} filtered (score: {score})")
            return {
                "sent": False,
                "tier": tier,
                "webhook": None,
                "error": None,
                "reason": f"Low score: {score}"
            }
        
        webhook_url = self.tier_webhooks.get(tier)
        
        if not webhook_url:
            logger.warning(f"No webhook configured for tier {tier}")
            return {
                "sent": False,
                "tier": tier,
                "webhook": None,
                "error": "No webhook configured"
            }
        
        # Build tiered payload
        payload = self._build_payload(username, tweet, rating, tier)
        
        # Send with retry
        for attempt in range(3):
            try:
                response = await self.client.post(webhook_url, json=payload)
                
                if response.status_code == 204:
                    logger.info(f"Sent tier {tier} tweet from @{username} (score: {score})")
                    return {
                        "sent": True,
                        "tier": tier,
                        "webhook": webhook_url[:50] + "...",
                        "error": None
                    }
                elif response.status_code == 404:
                    logger.error(f"Webhook not found for tier {tier}")
                    return {
                        "sent": False,
                        "tier": tier,
                        "webhook": webhook_url[:50] + "...",
                        "error": "Webhook 404"
                    }
                else:
                    logger.warning(f"Discord error {response.status_code}")
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    return {
                        "sent": False,
                        "tier": tier,
                        "webhook": webhook_url[:50] + "...",
                        "error": f"HTTP {response.status_code}"
                    }
                    
            except httpx.TimeoutException:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                return {
                    "sent": False,
                    "tier": tier,
                    "webhook": webhook_url[:50] + "...",
                    "error": "Timeout"
                }
            except Exception as e:
                return {
                    "sent": False,
                    "tier": tier,
                    "webhook": webhook_url[:50] + "...",
                    "error": str(e)
                }
        
        return {
            "sent": False,
            "tier": tier,
            "webhook": webhook_url[:50] + "...",
            "error": "Max retries exceeded"
        }
    
    def _build_payload(self, username: str, tweet: Tweet, rating: dict, tier: int) -> dict:
        """Build Discord embed with rating info."""
        score = rating.get("score", 5)
        category = rating.get("category", "unknown")
        summary = rating.get("summary", tweet.text[:100])
        reason = rating.get("reason", "")
        
        # Tier colors
        colors = {
            1: 0x95a5a6,  # Gray (shouldn't be used)
            2: 0x3498db,  # Blue (standard)
            3: 0xf39c12,  # Orange (premium)
            4: 0xe74c3c,  # Red (urgent)
        }
        
        # Tier labels
        labels = {
            1: "🚫 FILTERED",
            2: "📊 STANDARD",
            3: "⭐ PREMIUM",
            4: "🚨 URGENT",
        }
        
        # Truncate text
        description = tweet.text
        if len(description) > self.MAX_TEXT_LENGTH:
            description = description[:self.MAX_TEXT_LENGTH - 3] + "..."
        
        # Format metrics
        likes = self._format_number(tweet.likes)
        retweets = self._format_number(tweet.retweets)
        replies = self._format_number(tweet.replies)
        
        # Build tweet URL
        tweet_url = f"https://twitter.com/{username}/status/{tweet.id}"
        
        embed = {
            "author": {
                "name": f"@{username} ({labels[tier]})",
                "url": f"https://twitter.com/{username}",
                "icon_url": f"https://unavatar.io/twitter/{username}"
            },
            "title": f"📈 Score: {score}/10 | Category: {category.upper()}",
            "url": tweet_url,
            "description": description,
            "color": colors[tier],
            "timestamp": tweet.created_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "fields": [
                {
                    "name": "📝 Summary",
                    "value": summary[:256] or "No summary",
                    "inline": False
                },
                {
                    "name": "❤️ Likes",
                    "value": likes,
                    "inline": True
                },
                {
                    "name": "🔁 Retweets",
                    "value": retweets,
                    "inline": True
                },
                {
                    "name": "💬 Replies",
                    "value": replies,
                    "inline": True
                }
            ],
            "footer": {
                "text": f"AI: {reason[:100]}" if reason else "AI Analyzed"
            }
        }
        
        # Add image if exists
        if tweet.media_urls:
            embed["image"] = {"url": tweet.media_urls[0]}
        
        # Add AI action as field if special
        action = rating.get("action", "send")
        if action != "send":
            embed["fields"].append({
                "name": "🤖 AI Action",
                "value": action.upper(),
                "inline": False
            })
        
        return {
            "username": f"Twitter Monitor - Tier {tier}",
            "avatar_url": "https://abs.twimg.com/icons/apple-touch-icon-192x192.png",
            "embeds": [embed]
        }
    
    def _format_number(self, n: int) -> str:
        """Format number (e.g., 1200 -> 1.2k)."""
        if n >= 1000000:
            return f"{n/1000000:.1f}M"
        elif n >= 1000:
            return f"{n/1000:.1f}k"
        return str(n)
