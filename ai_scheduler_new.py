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
from discord_verifier import discord_verifier


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
            
            # QUICK FILTER: Skip retweets immediately
            if tweet.text.startswith("RT @"):
                logger.debug(f"Skipping retweet from @{user.username}")
                continue
            
            # AI Analysis
            rating = None
            if self.enable_ai and analyzer:
                try:
                    rating = await analyzer.analyze_tweet(user.username, tweet)
                    logger.info(f"AI Rating for @{user.username}: {rating.score}/10")
                    
                    # Record rating
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
                except Exception as e:
                    logger.error(f"AI analysis failed: {e}")
                    rating = None
            
            # Route based on score
            if not rating:
                continue
            
            # Score 0-1: Filter
            if rating.score < 2:
                logger.info(f"🗑️ Filtered (score {rating.score}): @{user.username}")
                continue
            
            # Score 2+: Discord
            logger.info(f"📨 Score {rating.score}/10 → Discord: @{user.username}")
            try:
                result = await discord.send_tweet(
                    user.webhook_url, user.username, tweet,
                    {"score": rating.score, "category": rating.category, 
                     "summary": rating.summary, "action": "send", "reason": rating.reason}
                )
                if result["sent"]:
                    db.record_sent_tweet(
                        tweet_id=tweet.id, username=user.username,
                        channel_id=user.channel_id, text=tweet.text,
                        created_at=tweet.created_at
                    )
            except Exception as e:
                logger.error(f"Discord failed: {e}")
            
            # Score 5+: Telegram
            if rating.score >= 5 and settings.USE_TELEGRAM:
                logger.info(f"📱 Score {rating.score}/10 → Telegram: @{user.username}")
                try:
                    from telegram_bot import telegram_bot
                    telegram_result = await telegram_bot.send_urgent_tweet(
                        username=user.username, text=tweet.text, url=tweet.url,
                        metrics={"likes": tweet.likes, "retweets": tweet.retweets, "replies": tweet.replies}
                    )
                except Exception as e:
                    logger.error(f"Telegram failed: {e}")
        
        # Update last_tweet_id
        if newest_id > last_id:
            db.update_user_last_tweet(user.username, str(newest_id))
            logger.debug(f"Updated last_tweet_id for @{user.username} to {newest_id}")
