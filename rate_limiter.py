#!/usr/bin/env python3
"""Sequential notification queue - one tweet at a time with user response time."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class QueuedTweet:
    """A tweet waiting to be sent."""
    username: str
    tweet_id: str
    text: str
    score: int
    category: str
    summary: str
    reason: str
    received_at: datetime = field(default_factory=datetime.now)


class NotificationRateLimiter:
    """
    Sequential notification system - one tweet at a time.
    
    Strategy:
    - Send 1st urgent tweet immediately
    - Wait for MIN_DELAY_MINUTES between notifications
    - User can take time to respond (BUILD/INTERESTING/NOTHING)
    - Next tweet only sent after delay
    - Never batch - each gets individual attention
    """
    
    MIN_DELAY_MINUTES = 2  # Minimum time between WhatsApp notifications
    MAX_QUEUE_SIZE = 20    # Max tweets to queue
    
    def __init__(self):
        self.last_notification_time: Optional[datetime] = None
        self.queue: List[QueuedTweet] = []
        self._lock = asyncio.Lock()
        self._processing = False
    
    async def should_send_notification(self, username: str, tweet_id: str) -> bool:
        """Check if we should send a notification now or queue it."""
        async with self._lock:
            now = datetime.now()
            
            # Check if in cooldown
            if self.last_notification_time:
                elapsed = (now - self.last_notification_time).total_seconds() / 60
                if elapsed < self.MIN_DELAY_MINUTES:
                    logger.info(
                        f"In delay period ({elapsed:.1f}min/{self.MIN_DELAY_MINUTES}min), "
                        f"queuing tweet from @{username} (#{len(self.queue)+1} in queue)"
                    )
                    return False
            
            return True
    
    async def queue_tweet(
        self,
        username: str,
        tweet_id: str,
        text: str,
        score: int,
        category: str,
        summary: str,
        reason: str
    ) -> int:
        """Add tweet to queue. Returns queue position."""
        async with self._lock:
            # Check for duplicates
            for existing in self.queue:
                if existing.tweet_id == tweet_id:
                    logger.debug(f"Tweet {tweet_id} already queued, skipping")
                    return -1
            
            # Add to queue (sorted by score, highest first)
            queued = QueuedTweet(
                username=username,
                tweet_id=tweet_id,
                text=text,
                score=score,
                category=category,
                summary=summary,
                reason=reason
            )
            
            # Insert in score order (highest first)
            inserted = False
            for i, existing in enumerate(self.queue):
                if score > existing.score:
                    self.queue.insert(i, queued)
                    inserted = True
                    break
            
            if not inserted:
                self.queue.append(queued)
            
            position = len(self.queue)
            
            # Trim if too many (remove lowest score)
            if len(self.queue) > self.MAX_QUEUE_SIZE:
                removed = self.queue.pop()  # Remove lowest score (end of list)
                logger.warning(f"Queue full, removed lowest score tweet from @{removed.username} ({removed.score}/10)")
            
            logger.info(f"Queued tweet from @{username} (score {score}, position in queue: {position})")
            return position
    
    async def get_next_tweet(self) -> Optional[QueuedTweet]:
        """Get next tweet from queue (highest score)."""
        async with self._lock:
            if not self.queue:
                return None
            return self.queue.pop(0)  # Remove and return highest score
    
    async def mark_notification_sent(self):
        """Mark that we just sent a notification."""
        async with self._lock:
            self.last_notification_time = datetime.now()
            logger.info(f"Notification sent, next one allowed in {self.MIN_DELAY_MINUTES}min")
    
    async def get_queue_status(self) -> dict:
        """Get current queue status."""
        async with self._lock:
            if not self.queue:
                return {"empty": True}
            
            return {
                "empty": False,
                "size": len(self.queue),
                "next_up": {
                    "username": self.queue[0].username,
                    "score": self.queue[0].score,
                    "summary": self.queue[0].summary[:100]
                },
                "all_queued": [
                    {
                        "username": t.username,
                        "score": t.score,
                        "category": t.category
                    }
                    for t in self.queue[:5]  # Show top 5
                ]
            }
    
    def get_status(self) -> dict:
        """Get current rate limiter status."""
        now = datetime.now()
        
        if self.last_notification_time:
            elapsed = (now - self.last_notification_time).total_seconds() / 60
            delay_remaining = max(0, self.MIN_DELAY_MINUTES - elapsed)
            in_delay = delay_remaining > 0
        else:
            delay_remaining = 0
            in_delay = False
        
        return {
            "in_delay_period": in_delay,
            "delay_remaining_minutes": round(delay_remaining, 1),
            "delay_total_minutes": self.MIN_DELAY_MINUTES,
            "queue_size": len(self.queue),
            "max_queue_size": self.MAX_QUEUE_SIZE,
            "next_notification_available": not in_delay and len(self.queue) == 0,
            "last_notification": self.last_notification_time.isoformat() if self.last_notification_time else None
        }


# Singleton instance
rate_limiter = NotificationRateLimiter()
