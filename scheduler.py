"""Background monitoring scheduler for Twitter Monitor Bot."""

import asyncio
import signal
from typing import List, Optional

import httpx
from loguru import logger

from config import settings
from database import db
from discord_client import DiscordClient, DiscordWebhookError
from models import Tweet, UserWithChannel
from twitter_client import (
    TwitterAuthError,
    TwitterClient,
    TwitterNotFoundError,
    TwitterRateLimitError,
)


class Scheduler:
    """Monitors Twitter users and sends new tweets to Discord."""
    
    def __init__(self, interval: int = None):
        self.interval = interval or settings.CHECK_INTERVAL_SECONDS
        self.running = False
        self._shutdown_event = asyncio.Event()
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_USERS)
    
    async def _process_user(
        self,
        user: UserWithChannel,
        twitter: TwitterClient,
        discord: DiscordClient
    ) -> None:
        """Process a single user - fetch tweets and send to Discord."""
        async with self._semaphore:
            logger.debug(f"Processing user: @{user.username}")
            
            try:
                # Fetch tweets
                tweets = await twitter.get_last_tweets(user.username)
                
                if not tweets:
                    logger.debug(f"No tweets found for @{user.username}")
                    return
                
                # Handle new user (no last_tweet_id)
                if user.last_tweet_id is None:
                    await self._handle_new_user(user, tweets)
                    return
                
                # Handle existing user - find new tweets
                await self._handle_existing_user(user, tweets, discord)
            
            except TwitterNotFoundError:
                logger.warning(f"User @{user.username} not found, marking as inactive")
                db.set_user_inactive(user.username)
            
            except TwitterAuthError:
                logger.error("Twitter API authentication failed")
                raise  # Re-raise to stop the scheduler
            
            except TwitterRateLimitError:
                logger.warning("Rate limit reached, will retry on next cycle")
            
            except Exception as e:
                logger.error(f"Error processing @{user.username}: {e}")
    
    async def _handle_new_user(
        self,
        user: UserWithChannel,
        tweets: List[Tweet]
    ) -> None:
        """Handle new user - set last_tweet_id without sending."""
        # Get the most recent tweet ID (tweets are sorted newest first by API)
        newest_tweet = max(tweets, key=lambda t: int(t.id))
        
        # Update last_tweet_id
        db.update_user_last_tweet_id(user.username, newest_tweet.id)
        
        logger.info(
            f"Initialized @{user.username} with last_tweet_id={newest_tweet.id} "
            f"(no tweets sent to prevent spam)"
        )
    
    async def _handle_existing_user(
        self,
        user: UserWithChannel,
        tweets: List[Tweet],
        discord: DiscordClient
    ) -> None:
        """Handle existing user - send new tweets to Discord."""
        # Filter tweets newer than last_tweet_id
        last_id = int(user.last_tweet_id)
        new_tweets = [t for t in tweets if int(t.id) > last_id]
        
        if not new_tweets:
            logger.debug(f"No new tweets for @{user.username}")
            return
        
        # Sort by created_at ascending (oldest first)
        new_tweets.sort(key=lambda t: t.created_at)
        
        logger.info(
            f"Found {len(new_tweets)} new tweet(s) from @{user.username}"
        )
        
        newest_id = last_id
        
        for tweet in new_tweets:
            # Update newest_id
            tweet_id_int = int(tweet.id)
            if tweet_id_int > newest_id:
                newest_id = tweet_id_int
            
            # Check if already sent (secondary deduplication)
            if db.is_tweet_sent(tweet.id, user.channel_id):
                logger.debug(f"Tweet {tweet.id} already sent, skipping")
                continue
            
            # Send to Discord
            try:
                success = await discord.send_tweet(
                    user.webhook_url,
                    user.username,
                    tweet
                )
                
                if success:
                    # Record in database
                    db.record_sent_tweet(
                        tweet_id=tweet.id,
                        username=user.username,
                        channel_id=user.channel_id,
                        text=tweet.text,
                        created_at=tweet.created_at
                    )
                    
                    logger.info(
                        f"Sent tweet {tweet.id} from @{user.username} to channel"
                    )
                    
                    # Rate limit protection between sends
                    await asyncio.sleep(1)
                
                else:
                    logger.error(
                        f"Failed to send tweet {tweet.id} from @{user.username}"
                    )
            
            except DiscordWebhookError as e:
                if "404" in str(e):
                    logger.error(
                        f"Webhook 404 for user @{user.username}, disabling channel"
                    )
                    db.set_channel_inactive(user.channel_id)
                else:
                    logger.error(f"Discord error for @{user.username}: {e}")
        
        # Update last_tweet_id
        if newest_id > last_id:
            db.update_user_last_tweet_id(user.username, str(newest_id))
            logger.debug(f"Updated last_tweet_id for @{user.username} to {newest_id}")
    
    async def run_once(self) -> None:
        """Run a single monitoring cycle."""
        logger.info("Starting monitoring cycle...")
        
        # Get active users
        users = db.get_active_users_with_channels()
        
        if not users:
            logger.info("No active users to monitor")
            return
        
        logger.info(f"Monitoring {len(users)} user(s)...")
        
        # Process all users concurrently
        async with TwitterClient() as twitter, DiscordClient() as discord:
            tasks = [
                self._process_user(user, twitter, discord)
                for user in users
            ]
            
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except TwitterAuthError:
                logger.error("Invalid Twitter API key. Stopping.")
                raise
        
        logger.info("Monitoring cycle completed")
    
    async def _self_ping(self) -> None:
        """Ping our own health endpoint every 10 min to keep Render awake."""
        # Use localhost for internal ping
        health_url = "http://localhost:8000/api/health"
        
        while self.running:
            try:
                await asyncio.sleep(600)  # 10 minutes
                if not self.running:
                    break
                    
                async with httpx.AsyncClient() as client:
                    response = await client.get(health_url, timeout=10)
                    if response.status_code == 200:
                        logger.debug("Self-ping successful - keeping Render awake")
                    else:
                        logger.warning(f"Self-ping failed: {response.status_code}")
            except Exception as e:
                logger.debug(f"Self-ping error (Render might be sleeping): {e}")
    
    async def run(self) -> None:
        """Run continuous monitoring loop."""
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._signal_handler)
        
        logger.info(f"Starting monitor loop with {self.interval}s interval")
        
        # Start self-ping task to keep Render awake
        ping_task = asyncio.create_task(self._self_ping())
        
        try:
            while self.running:
                cycle_start = asyncio.get_event_loop().time()
                
                try:
                    await self.run_once()
                except TwitterAuthError:
                    logger.error("Authentication failed. Exiting.")
                    break
                except Exception as e:
                    logger.error(f"Error in monitoring cycle: {e}")
                
                # Calculate sleep time
                elapsed = asyncio.get_event_loop().time() - cycle_start
                sleep_time = max(0, self.interval - elapsed)
                
                if sleep_time > 0 and self.running:
                    logger.debug(f"Sleeping for {sleep_time:.1f}s...")
                    try:
                        await asyncio.wait_for(
                            self._shutdown_event.wait(),
                            timeout=sleep_time
                        )
                    except asyncio.TimeoutError:
                        pass  # Normal timeout, continue loop
        
        finally:
            self.running = False
            ping_task.cancel()
            logger.info("Monitor loop stopped")
    
    def _signal_handler(self) -> None:
        """Handle shutdown signals."""
        logger.info("Shutdown signal received, stopping...")
        self.running = False
        self._shutdown_event.set()
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        self._shutdown_event.set()


async def run_scheduler(interval: Optional[int] = None) -> None:
    """Entry point for running the scheduler."""
    scheduler = Scheduler(interval=interval)
    await scheduler.run()


async def run_once() -> None:
    """Entry point for single execution (cron jobs)."""
    scheduler = Scheduler()
    await scheduler.run_once()
