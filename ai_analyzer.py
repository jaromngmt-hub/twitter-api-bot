"""AI-powered tweet analyzer for rating content importance."""

import json
from typing import Optional

import httpx
from loguru import logger

from config import settings
from models import Tweet


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
    """Analyzes tweets using OpenAI API for importance rating."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def analyze_tweet(self, username: str, tweet: Tweet) -> TweetRating:
        """
        Analyze a tweet and return importance rating 1-10.
        
        Rating scale:
        1-3: Low value (fluff, greetings, spam)
        4-6: Medium value (general updates, community chat)
        7-8: High value (news, insights, useful info)
        9-10: Critical value (alpha, breaking news, opportunities)
        """
        if not self.api_key:
            logger.warning("No OpenAI API key, returning default rating")
            return TweetRating(
                score=5,
                category="unknown",
                summary=tweet.text[:100],
                action="send",
                reason="No AI analysis available"
            )
        
        prompt = self._build_prompt(username, tweet)
        
        try:
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert crypto/tech analyst. Rate tweets on importance (1-10). Be strict - most tweets are fluff."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            return self._parse_response(content, tweet)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API error: {e}")
            raise AIAnalyzerError(f"API error: {e}")
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

TWEET: """{tweet.text}"""

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
            # Try to parse as JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            return TweetRating(
                score=max(1, min(10, int(data.get("score", 5)))),
                category=data.get("category", "unknown"),
                summary=data.get("summary", tweet.text[:100]),
                action=data.get("action", "send"),
                reason=data.get("reason", "No reason provided")
            )
            
        except json.JSONDecodeError:
            # Fallback if not valid JSON
            logger.warning(f"Could not parse AI response as JSON: {content}")
            
            # Extract score if possible
            score = 5
            if "score" in content.lower():
                import re
                match = re.search(r'score["\']?\s*:\s*(\d+)', content)
                if match:
                    score = int(match.group(1))
            
            return TweetRating(
                score=score,
                category="unknown",
                summary=tweet.text[:100],
                action="send",
                reason="Could not parse AI response"
            )


# Pydantic model for TweetRating
from pydantic import BaseModel

class TweetRating(BaseModel):
    """Rating result for a tweet."""
    score: int
    category: str
    summary: str
    action: str
    reason: str
