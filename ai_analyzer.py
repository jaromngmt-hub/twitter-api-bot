"""AI-powered tweet analyzer for rating content importance.

USING OUR ai_router with DeepSeek V3.2 - NOT direct OpenAI!
"""

import json
import re
from typing import Optional

import httpx
from loguru import logger
from pydantic import BaseModel

from config import settings
from models import Tweet
from ai_router import ai_router


class AIAnalyzerError(Exception):
    """AI analysis error."""
    pass


class TweetRating(BaseModel):
    """Rating result for a tweet."""
    score: int  # 1-10
    category: str  # "bot", "alpha", "community", "news", "fluff", etc.
    summary: str  # Brief summary of content
    action: str  # "send", "filter", "highlight", "follow_user"
    reason: str  # Why this rating was given


class AIAnalyzer:
    """Analyzes tweets using OUR ai_router (DeepSeek/Kimi), NOT OpenAI directly!"""
    
    def __init__(self, api_key: str = None):
        self.ai_router = ai_router
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def analyze_tweet(self, username: str, tweet: Tweet) -> TweetRating:
        """
        Analyze a tweet using DeepSeek V3.2 via our ai_router.
        
        Rating scale:
        1-3: Low value (fluff, greetings, spam)
        4-6: Medium value (general updates, community chat)
        7-8: High value (news, insights, useful info)
        9-10: Critical value (alpha, breaking news, opportunities)
        """
        # QUICK FILTER: Retweets are NEVER valuable
        if tweet.text.strip().upper().startswith("RT @"):
            return TweetRating(
                score=1,
                category="retweet",
                summary="Retweet - filtered",
                action="filter",
                reason="Retweets are not original content"
            )
        
        prompt = self._build_prompt(username, tweet)
        
        try:
            # Use OUR ai_router with DeepSeek V3.2!
            response = await self.ai_router.generate(
                prompt=prompt,
                task_type="analysis",  # Uses DeepSeek V3.2
                temperature=0.3,
                max_tokens=500
            )
            
            return self._parse_response(response, tweet)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Return default rating on error
            return TweetRating(
                score=5,
                category="error",
                summary=tweet.text[:100],
                action="send",
                reason=f"Analysis failed: {e}"
            )
    
    def _build_prompt(self, username: str, tweet: Tweet) -> str:
        """Build the analysis prompt."""
        return f"""Analyze this tweet from @{username}:

TWEET: {tweet.text}

METRICS:
- Likes: {tweet.likes}
- Retweets: {tweet.retweets}
- Replies: {tweet.replies}

Rate this tweet 1-10 based on IMPORTANCE and VALUE:

SCORING GUIDE:
1-3: Fluff, greetings, spam, "gm", "welcome", basic community chat
4-5: Minor updates, personal thoughts, low-impact announcements
6-7: Useful info, news, market commentary, decent insights
8-9: High-value alpha, breaking news, trading signals, major announcements
10: Critical alpha, life-changing info, major opportunities

Also classify:
- CATEGORY: bot | alpha | news | community | fluff | question | giveaway
- ACTION: send | filter | highlight | follow_user | build_bot

Respond in JSON format:
{{
    "score": 7,
    "category": "alpha",
    "summary": "Brief 10-word summary",
    "action": "highlight",
    "reason": "Why this rating?"
}}"""
    
    def _parse_response(self, content: str, tweet: Tweet) -> TweetRating:
        """Parse AI response into TweetRating."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(content)
            
            return TweetRating(
                score=data.get("score", 5),
                category=data.get("category", "unknown"),
                summary=data.get("summary", tweet.text[:100]),
                action=data.get("action", "send"),
                reason=data.get("reason", "AI analyzed")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            # Fallback: try to extract score from text
            score_match = re.search(r'(\d+)', content)
            score = int(score_match.group(1)) if score_match else 5
            
            return TweetRating(
                score=min(max(score, 1), 10),
                category="unknown",
                summary=tweet.text[:100],
                action="send",
                reason=f"Parse error: {content[:100]}"
            )


# Global instance
analyzer: Optional[AIAnalyzer] = None


def init_analyzer():
    """Initialize the global analyzer."""
    global analyzer
    analyzer = AIAnalyzer()
    return analyzer
