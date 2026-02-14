"""TwitterAPI.io client for fetching tweets."""

import asyncio
from datetime import datetime
from typing import List, Optional

import httpx
from loguru import logger

from config import settings
from models import Tweet


class TwitterAPIError(Exception):
    """Twitter API error."""
    pass


class TwitterAuthError(TwitterAPIError):
    """Authentication error (401)."""
    pass


class TwitterRateLimitError(TwitterAPIError):
    """Rate limit error (429)."""
    pass


class TwitterNotFoundError(TwitterAPIError):
    """User not found error (404)."""
    pass


class TwitterClient:
    """Async client for TwitterAPI.io."""
    
    BASE_URL = settings.TWITTERAPI_BASE_URL
    MAX_RETRIES = 3
    BACKOFF_DELAYS = [2, 4, 8]  # Exponential backoff delays in seconds
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.TWITTERAPI_KEY
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.TWITTERAPI_TIMEOUT),
            headers={
                "x-api-key": self.api_key,
                "Accept": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _make_request(
        self,
        endpoint: str,
        params: dict = None,
        retry_count: int = 0
    ) -> dict:
        """Make HTTP request with error handling and retry logic."""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            
            elif response.status_code == 401:
                logger.error("TwitterAPI returned 401 - Invalid API Key")
                raise TwitterAuthError("Invalid API Key")
            
            elif response.status_code == 404:
                logger.warning(f"User not found (404): {params}")
                raise TwitterNotFoundError("User not found")
            
            elif response.status_code == 429:
                if retry_count < len(self.BACKOFF_DELAYS):
                    delay = self.BACKOFF_DELAYS[retry_count]
                    logger.warning(f"Rate limited (429). Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    return await self._make_request(endpoint, params, retry_count + 1)
                else:
                    logger.error("Rate limit exceeded. Max retries reached.")
                    raise TwitterRateLimitError("Rate limit exceeded")
            
            else:
                response.raise_for_status()
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            raise TwitterAPIError(f"HTTP {e.response.status_code}: {e}")
        
        except httpx.RequestError as e:
            if retry_count < self.MAX_RETRIES:
                logger.warning(f"Network error: {e}. Retrying...")
                await asyncio.sleep(1)
                return await self._make_request(endpoint, params, retry_count + 1)
            raise TwitterAPIError(f"Network error after {self.MAX_RETRIES} retries: {e}")
    
    async def get_last_tweets(
        self,
        username: str,
        max_results: int = None
    ) -> List[Tweet]:
        """Fetch last tweets for a user."""
        max_results = max_results or settings.MAX_TWEETS_PER_CHECK
        
        params = {
            "userName": username,
            "max_results": max_results
        }
        
        try:
            data = await self._make_request("/twitter/user/last_tweets", params)
            return self._parse_tweets(data)
        
        except TwitterNotFoundError:
            # Return empty list, caller should handle user not found
            return []
        
        except (TwitterAuthError, TwitterRateLimitError):
            raise
        
        except TwitterAPIError as e:
            logger.error(f"Failed to fetch tweets for @{username}: {e}")
            return []
    
    def _parse_tweets(self, data: dict) -> List[Tweet]:
        """Parse API response into Tweet models."""
        tweets = []
        
        if not data or not isinstance(data, dict):
            return tweets
        
        # Handle nested data structure
        tweet_data = data.get("data", data)
        if isinstance(tweet_data, dict):
            tweet_list = tweet_data.get("tweets", [])
        elif isinstance(tweet_data, list):
            tweet_list = tweet_data
        else:
            tweet_list = []
        
        for tweet_dict in tweet_list:
            try:
                tweet = self._parse_single_tweet(tweet_dict)
                if tweet:
                    tweets.append(tweet)
            except Exception as e:
                logger.warning(f"Failed to parse tweet: {e}")
                continue
        
        return tweets
    
    def _parse_single_tweet(self, data: dict) -> Optional[Tweet]:
        """Parse a single tweet from API response."""
        if not data or not isinstance(data, dict):
            return None
        
        tweet_id = str(data.get("id", ""))
        text = data.get("text", "")
        
        if not tweet_id or not text:
            return None
        
        # Parse created_at
        created_at_str = data.get("created_at", "")
        try:
            # Handle ISO format
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            created_at = datetime.utcnow()
        
        # Parse metrics
        metrics = data.get("public_metrics", {})
        likes = metrics.get("like_count", 0)
        retweets = metrics.get("retweet_count", 0)
        replies = metrics.get("reply_count", 0)
        
        # Parse media URLs
        media_urls = []
        entities = data.get("entities", {})
        media_list = entities.get("media", [])
        
        for media in media_list:
            if media.get("type") == "photo":
                url = media.get("url") or media.get("media_url_https")
                if url:
                    media_urls.append(url)
            elif media.get("type") in ("video", "animated_gif"):
                # For videos, use thumbnail if available
                thumbnail = media.get("preview_image_url") or media.get("media_url_https")
                if thumbnail:
                    media_urls.append(thumbnail)
        
        # Build tweet URL (Twitter format)
        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
        
        return Tweet(
            id=tweet_id,
            text=text,
            created_at=created_at,
            likes=likes,
            retweets=retweets,
            replies=replies,
            url=tweet_url,
            media_urls=media_urls
        )
