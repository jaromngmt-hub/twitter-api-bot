#!/usr/bin/env python3
"""Rate limiter for urgent notifications to prevent spam."""

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
    Rate limits urgent notifications to prevent spam.
    
    Strategy:
    - Max 1 notification per COOLDOWN_MINUTES
    - If multiple urgent tweets arrive, queue them
    - Send summary after cooldown expires
    - User can still see all in Discord
    """
    
    COOLDOWN_MINUTES = 15  # Minimum time between WhatsApp notifications
    MAX_QUEUE_SIZE = 10    # Max tweets to queue
    BATCH_SUMMARY_AFTER = 3  # If 3+ queued, send summary instead of individual
    
    def __init__(self):
        self.last_notification_time: Optional[datetime] = None
        self.queue: List[QueuedTweet] = []
        self._lock = asyncio.Lock()
        self._cooldown_task: Optional[asyncio.Task] = None
    
    async def should_send_notification(self, username: str, tweet_id: str) -> bool:
        """Check if we should send a notification now or queue it."""
        async with self._lock:
            now = datetime.now()
            
            # Check if in cooldown
            if self.last_notification_time:
                elapsed = (now - self.last_notification_time).total_seconds() / 60
                if elapsed < self.COOLDOWN_MINUTES:
                    logger.info(
                        f"In cooldown ({elapsed:.1f}min/{self.COOLDOWN_MINUTES}min), "
                        f"queuing tweet from @{username}"
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
            
            # Add to queue
            queued = QueuedTweet(
                username=username,
                tweet_id=tweet_id,
                text=text,
                score=score,
                category=category,
                summary=summary,
                reason=reason
            )
            
            self.queue.append(queued)
            position = len(self.queue)
            
            # Trim if too many
            if len(self.queue) > self.MAX_QUEUE_SIZE:
                removed = self.queue.pop(0)  # Remove oldest
                logger.warning(f"Queue full, removed oldest tweet from @{removed.username}")
            
            logger.info(f"Queued tweet from @{username} (position {position}, queue size: {len(self.queue)})")
            return position
    
    async def mark_notification_sent(self):
        """Mark that we just sent a notification."""
        async with self._lock:
            self.last_notification_time = datetime.now()
            self._start_cooldown_timer()
    
    def _start_cooldown_timer(self):
        """Start timer to process queue after cooldown."""
        if self._cooldown_task and not self._cooldown_task.done():
            self._cooldown_task.cancel()
        
        self._cooldown_task = asyncio.create_task(self._process_queue_after_cooldown())
    
    async def _process_queue_after_cooldown(self):
        """Wait for cooldown then process queued tweets."""
        await asyncio.sleep(self.COOLDOWN_MINUTES * 60)
        
        async with self._lock:
            if not self.queue:
                return
            
            logger.info(f"Cooldown expired, processing {len(self.queue)} queued tweets")
    
    async def get_queued_summary(self) -> Optional[dict]:
        """Get summary of queued tweets for batch notification."""
        async with self._lock:
            if not self.queue:
                return None
            
            # Sort by score (highest first)
            sorted_queue = sorted(self.queue, key=lambda x: x.score, reverse=True)
            
            # Get top tweets
            top_tweets = sorted_queue[:5]  # Top 5
            total_queued = len(self.queue)
            avg_score = sum(t.score for t in self.queue) / len(self.queue)
            
            return {
                "total": total_queued,
                "top_tweets": [
                    {
                        "username": t.username,
                        "score": t.score,
                        "category": t.category,
                        "summary": t.summary[:100]
                    }
                    for t in top_tweets
                ],
                "avg_score": round(avg_score, 1),
                "highest_score": sorted_queue[0].score if sorted_queue else 0
            }
    
    async def clear_queue(self):
        """Clear the queue after processing."""
        async with self._lock:
            cleared = len(self.queue)
            self.queue.clear()
            logger.info(f"Cleared {cleared} tweets from queue")
            return cleared
    
    async def get_next_batch(self, max_size: int = 3) -> List[QueuedTweet]:
        """Get next batch of tweets to process."""
        async with self._lock:
            batch = self.queue[:max_size]
            self.queue = self.queue[max_size:]
            return batch
    
    def get_status(self) -> dict:
        """Get current rate limiter status."""
        now = datetime.now()
        
        if self.last_notification_time:
            elapsed = (now - self.last_notification_time).total_seconds() / 60
            cooldown_remaining = max(0, self.COOLDOWN_MINUTES - elapsed)
            in_cooldown = cooldown_remaining > 0
        else:
            cooldown_remaining = 0
            in_cooldown = False
        
        return {
            "in_cooldown": in_cooldown,
            "cooldown_remaining_minutes": round(cooldown_remaining, 1),
            "cooldown_total_minutes": self.COOLDOWN_MINUTES,
            "queue_size": len(self.queue),
            "max_queue_size": self.MAX_QUEUE_SIZE,
            "last_notification": self.last_notification_time.isoformat() if self.last_notification_time else None
        }


# Singleton instance
rate_limiter = NotificationRateLimiter()
