"""AI-powered background monitoring scheduler with tiered routing."""

import asyncio
import signal
from typing import List, Optional

from loguru import logger

from action_handler import ActionHandler
from ai_analyzer import AIAnalyzer, TweetRating
from config import settings
from database import db
from models import Tweet, UserWithChannel
from rate_limiter import rate_limiter
from tiered_discord_client import TieredDiscordClient
from twitter_client import (
    TwitterAuthError,
    TwitterClient,
    TwitterNotFoundError,
    TwitterRateLimitError,
)
from urgent_notifier import UrgentNotifier
from whatsapp_handler import whatsapp_handler


class AIScheduler:
    """
    AI-powered monitor that rates tweets and routes by importance.
    
    Features:
    - AI analysis of every tweet (1-10 score)
    - Tiered Discord routing (Standard/Premium/Urgent)
    - Automatic filtering of low-value content
    - Future action detection (build_bot, follow_user, etc.)
    """
    
    def __init__(self, interval: int = None):
        self.interval = interval or settings.CHECK_INTERVAL_SECONDS
        self.running = False
        self._shutdown_event = asyncio.Event()
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_USERS)
        self.enable_ai = settings.ENABLE_AI_ANALYSIS
        self.min_score = settings.AI_MIN_SCORE_TO_SEND
    
    async def _process_user(
        self,
        user: UserWithChannel,
        twitter: TwitterClient,
        discord: TieredDiscordClient,
        analyzer: Optional[AIAnalyzer] = None,
        urgent_notifier: Optional[UrgentNotifier] = None
    ) -> None:
        """Process a single user with AI analysis."""
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
                
                # Handle existing user with AI analysis
                await self._handle_existing_user(user, tweets, discord, analyzer)
            
            except TwitterNotFoundError:
                logger.warning(f"User @{user.username} not found, marking as inactive")
                db.set_user_inactive(user.username)
            
            except TwitterAuthError:
                logger.error("Twitter API authentication failed")
                raise
            
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
        newest_tweet = max(tweets, key=lambda t: int(t.id))
        db.update_user_last_tweet_id(user.username, newest_tweet.id)
        logger.info(
            f"Initialized @{user.username} with last_tweet_id={newest_tweet.id} "
            f"(no tweets sent to prevent spam)"
        )
    
    async def _handle_existing_user(
        self,
        user: UserWithChannel,
        tweets: List[Tweet],
        discord: TieredDiscordClient,
        analyzer: Optional[AIAnalyzer] = None
    ) -> None:
        """Handle existing user with AI-powered routing."""
        # Filter tweets newer than last_tweet_id
        last_id = int(user.last_tweet_id)
        new_tweets = [t for t in tweets if int(t.id) > last_id]
        
        if not new_tweets:
            logger.debug(f"No new tweets for @{user.username}")
            return
        
        # Sort by created_at ascending (oldest first)
        new_tweets.sort(key=lambda t: t.created_at)
        
        logger.info(f"Found {len(new_tweets)} new tweet(s) from @{user.username}")
        
        newest_id = last_id
        
        for tweet in new_tweets:
            tweet_id_int = int(tweet.id)
            if tweet_id_int > newest_id:
                newest_id = tweet_id_int
            
            # Check if already sent
            if db.is_tweet_sent(tweet.id, user.channel_id):
                logger.debug(f"Tweet {tweet.id} already sent, skipping")
                continue
            
            # AI Analysis (if enabled)
            rating = None
            if self.enable_ai and analyzer:
                try:
                    rating = await analyzer.analyze_tweet(user.username, tweet)
                    logger.info(
                        f"AI Rating for @{user.username}: "
                        f"{rating.score}/10 ({rating.category}) - {rating.action}"
                    )
                    
                    # Record rating in database
                    db.record_tweet_rating(
                        tweet_id=tweet.id,
                        username=user.username,
                        channel_id=user.channel_id,
                        score=rating.score,
                        category=rating.category,
                        summary=rating.summary,
                        action=rating.action,
                        reason=rating.reason
                    )
                    
                    # Handle special AI actions
                    await self._handle_ai_action(rating, user, tweet)
                    
                except Exception as e:
                    logger.error(f"AI analysis failed: {e}")
                    # Continue with default rating
                    rating = None
            
            # Route tweets based on AI score
            if self.enable_ai and rating:
                # 0-1: Filter completely (useless)
                if rating.score < 2:
                    logger.info(f"🗑️ Tweet from @{user.username} filtered (score: {rating.score}/10)")
                    continue
                
                # 2-7: Send to Discord (categorized by topic: AI, CRYPTO, etc.)
                elif rating.score < 8:
                    result = await discord.send_tweet(
                        user.username,
                        tweet,
                        {"score": rating.score, "category": rating.category, 
                         "summary": rating.summary, "action": rating.action, 
                         "reason": rating.reason}
                    )
                    
                    if result["sent"]:
                        db.record_sent_tweet(
                            tweet_id=tweet.id,
                            username=user.username,
                            channel_id=user.channel_id,
                            text=tweet.text,
                            created_at=tweet.created_at
                        )
                        logger.info(f"📨 Sent to Discord: {rating.category} tweet (score {rating.score}) from @{user.username}")
                
                # 8-10: WhatsApp for user decision (ALL categories go here)
                else:
                    logger.info(f"🚨 HIGH VALUE tweet from @{user.username} (score: {rating.score}/10) → WhatsApp")
                    
                    # Send WhatsApp notification for user to decide
                    if urgent_notifier:
                        try:
                            should_send = await rate_limiter.should_send_notification(
                                user.username, tweet.id
                            )
                            
                            if should_send:
                                notify_result = await urgent_notifier.send_urgent_notification(
                                    user.username,
                                    tweet,
                                    {
                                        "score": rating.score,
                                        "category": rating.category,
                                        "summary": rating.summary,
                                        "reason": rating.reason
                                    }
                                )
                                
                                if notify_result["sent"]:
                                    logger.info(f"📱 WhatsApp sent for @{user.username} (score: {rating.score})")
                                    await rate_limiter.mark_notification_sent()
                                    
                                    # Store for user reply (BUILD/INTERESTING/NOTHING)
                                    whatsapp_handler.store_pending_tweet(
                                        phone=settings.YOUR_PHONE_NUMBER,
                                        username=user.username,
                                        tweet=tweet,
                                        rating={
                                            "score": rating.score,
                                            "category": rating.category,
                                            "summary": rating.summary,
                                            "reason": rating.reason
                                        }
                                    )
                                else:
                                    logger.warning(f"WhatsApp failed: {notify_result}")
                            else:
                                # Queue for later
                                position = await rate_limiter.queue_tweet(
                                    username=user.username,
                                    tweet_id=tweet.id,
                                    text=tweet.text,
                                    score=rating.score,
                                    category=rating.category,
                                    summary=rating.summary,
                                    reason=rating.reason
                                )
                                logger.info(f"⏳ Queued for WhatsApp: @{user.username} (position {position})")
                                
                        except Exception as e:
                            logger.error(f"WhatsApp error: {e}")
            
            else:
                # Legacy mode - no AI, send all to default webhook
                result = await discord.send_tweet(
                    user.webhook_url,
                    user.username,
                    tweet,
                    {"score": 5, "category": "legacy", "summary": tweet.text[:100],
                     "action": "send", "reason": "AI disabled"}
                )
                
                if result["sent"]:
                    db.record_sent_tweet(
                        tweet_id=tweet.id,
                        username=user.username,
                        channel_id=user.channel_id,
                        text=tweet.text,
                        created_at=tweet.created_at
                    )
                    logger.info(f"📨 Legacy mode: Sent tweet from @{user.username}")
            
            # Rate limit protection
            await asyncio.sleep(1)
        
        # Update last_tweet_id
        if newest_id > last_id:
            db.update_user_last_tweet_id(user.username, str(newest_id))
            logger.debug(f"Updated last_tweet_id for @{user.username} to {newest_id}")
    
    async def _handle_ai_action(self, rating: TweetRating, user: UserWithChannel, tweet: Tweet) -> None:
        """Handle special AI-detected actions."""
        action = rating.action.lower()
        
        if action == "filter":
            logger.info(f"AI decided to filter tweet from @{user.username}")
            return
        
        elif action == "build_bot":
            logger.info(f"🤖 AI detected bot opportunity from @{user.username}!")
            logger.info(f"   Tweet: {tweet.text[:100]}...")
            # TODO: Implement bot building logic
            # This is where you'd integrate with your bot builder
            
        elif action == "follow_user":
            logger.info(f"👤 AI suggests following @{user.username}")
            # TODO: Implement auto-follow logic
            # This would require Twitter API v2 with write permissions
            
        elif action == "highlight":
            logger.info(f"⭐ AI highlighted important tweet from @{user.username}")
            # Already handled by tier routing
    
    async def run_once(self) -> None:
        """Run a single monitoring cycle with AI analysis."""
        logger.info("Starting AI-powered monitoring cycle...")
        
        users = db.get_active_users_with_channels()
        
        if not users:
            logger.info("No active users to monitor")
            return
        
        logger.info(f"Monitoring {len(users)} user(s) with AI analysis...")
        
        async with TwitterClient() as twitter:
            async with TieredDiscordClient() as discord:
                analyzer = None
                urgent_notifier = None
                
                if self.enable_ai:
                    try:
                        analyzer = AIAnalyzer()
                        logger.info("AI analyzer initialized")
                    except Exception as e:
                        logger.error(f"Failed to initialize AI analyzer: {e}")
                    
                    # Initialize urgent notifier for score 9-10
                    if settings.URGENT_NOTIFICATIONS_ENABLED:
                        try:
                            urgent_notifier = UrgentNotifier()
                            if urgent_notifier.is_configured():
                                logger.info(f"🚨 Urgent notifier initialized (min score: {settings.URGENT_MIN_SCORE})")
                            else:
                                logger.warning("Urgent notifications enabled but not configured")
                        except Exception as e:
                            logger.error(f"Failed to initialize urgent notifier: {e}")
                
                tasks = [
                    self._process_user(user, twitter, discord, analyzer, urgent_notifier)
                    for user in users
                ]
                
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except TwitterAuthError:
                    logger.error("Invalid Twitter API key. Stopping.")
                    raise
        
        logger.info("AI monitoring cycle completed")
    
    async def _process_notification_queue(self):
        """Background task to process queued notifications one by one."""
        while self.running:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            if not self.running:
                break
            
            try:
                status = rate_limiter.get_status()
                
                # Check if we can send next notification
                if status["in_delay_period"]:
                    continue  # Wait more
                
                # Get next tweet from queue
                next_tweet = await rate_limiter.get_next_tweet()
                if not next_tweet:
                    continue  # Queue empty
                
                logger.info(
                    f"Processing queued tweet from @{next_tweet.username} "
                    f"({next_tweet.score}/10), {status['queue_size']} remaining in queue"
                )
                
                # Send notification
                async with UrgentNotifier() as notifier:
                    if notifier.is_configured():
                        notify_result = await notifier.send_urgent_notification(
                            next_tweet.username,
                            None,  # We'll pass text directly
                            {
                                "score": next_tweet.score,
                                "category": next_tweet.category,
                                "summary": next_tweet.summary,
                                "reason": next_tweet.reason
                            }
                        )
                        
                        if notify_result["sent"]:
                            await rate_limiter.mark_notification_sent()
                            
                            # Create a temporary tweet object for pending storage
                            from models import Tweet
                            temp_tweet = Tweet(
                                id=next_tweet.tweet_id,
                                text=next_tweet.text,
                                created_at=datetime.now(),
                                author_id="0",
                                metrics={}
                            )
                            
                            # Store for user reply
                            whatsapp_handler.store_pending_tweet(
                                phone=settings.YOUR_PHONE_NUMBER,
                                username=next_tweet.username,
                                tweet=temp_tweet,
                                rating={
                                    "score": next_tweet.score,
                                    "category": next_tweet.category,
                                    "summary": next_tweet.summary,
                                    "reason": next_tweet.reason
                                }
                            )
                            
                            logger.info(
                                f"🚨 Queued notification sent for @{next_tweet.username} "
                                f"({next_tweet.score}/10), next in {rate_limiter.MIN_DELAY_MINUTES}min"
                            )
                        else:
                            logger.error(f"Failed to send queued notification: {notify_result}")
                            # Re-queue? For now, log and continue
                            
            except Exception as e:
                logger.error(f"Error in notification queue processor: {e}")
    
    async def run(self) -> None:
        """Run continuous AI-powered monitoring loop."""
        self.running = True
        
        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._signal_handler)
        
        logger.info(f"Starting AI scheduler with {self.interval}s interval")
        logger.info(f"AI Analysis: {'ENABLED' if self.enable_ai else 'DISABLED'}")
        if self.enable_ai:
            logger.info(f"Minimum score to send: {self.min_score}")
            logger.info(f"Urgent Notifications: {'ENABLED' if settings.URGENT_NOTIFICATIONS_ENABLED else 'DISABLED'}")
            if settings.URGENT_NOTIFICATIONS_ENABLED:
                logger.info(f"  → Min score for phone alert: {settings.URGENT_MIN_SCORE}")
                logger.info(f"  → Sequential mode: 1 per {rate_limiter.MIN_DELAY_MINUTES}min (no batching)")
        
        # Start background sequential notification processor
        queue_processor = asyncio.create_task(self._process_notification_queue())
        
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
                        pass
        
        finally:
            self.running = False
            queue_processor.cancel()
            logger.info("AI scheduler stopped")
    
    def _signal_handler(self) -> None:
        """Handle shutdown signals."""
        logger.info("Shutdown signal received, stopping...")
        self.running = False
        self._shutdown_event.set()
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        self._shutdown_event.set()


async def run_ai_scheduler(interval: Optional[int] = None) -> None:
    """Entry point for running the AI scheduler."""
    scheduler = AIScheduler(interval=interval)
    await scheduler.run()


async def run_ai_once() -> None:
    """Entry point for single AI-powered execution."""
    scheduler = AIScheduler()
    await scheduler.run_once()
