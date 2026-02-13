"""
Discord Tweet Verifier Agent

Weryfikuje tweety PRZED wysłaniem na Discord.
Odrzuca: RT, odpowiedzi, spam, słabe treści
Akceptuje: Tylko oryginalne, wartościowe tweety
"""

from dataclasses import dataclass
from typing import Optional
from loguru import logger

from ai_router import ai_router
from models import Tweet


@dataclass
class VerificationResult:
    """Wynik weryfikacji tweeta."""
    should_send: bool
    reason: str
    quality_score: int  # 0-10
    category: str  # ai, crypto, business, tech, etc.
    is_original_content: bool
    

class DiscordVerifierAgent:
    """
    Agent AI weryfikujący tweety przed wysłaniem na Discord.
    
    Odrzuca:
    - Retweety (RT @username)
    - Odpowiedzi (@username na początku)
    - Za krótkie (< 50 znaków)
    - Za mało engagementu (< 10 likes)
    - Spam, reklamy, shitposting
    - Tweet bez treści (same linki/media)
    
    Akceptuje:
    - Oryginalne myśli, wnioski
    - Porady, tutoriale
    - Analizy, case studies
    - Newsy (tylko ważne)
    """
    
    MIN_LENGTH = 50  # Min długość tweeta
    MIN_LIKES = 10   # Min polubień
    
    def __init__(self):
        self.enabled = True
    
    def _basic_filters(self, tweet: Tweet) -> tuple[bool, str]:
        """Szybkie filtry przed AI (performance)."""
        
        # 1. Retweet check
        if tweet.text.startswith("RT @"):
            return False, "Retweet - pomijamy"
        
        # 2. Reply check
        if tweet.text.startswith("@"):
            return False, "Odpowiedź - pomijamy"
        
        # 3. Too short
        if len(tweet.text) < self.MIN_LENGTH:
            return False, f"Za krótki ({len(tweet.text)} znaków)"
        
        # 4. Too low engagement
        if tweet.likes < self.MIN_LIKES:
            return False, f"Za mało likes ({tweet.likes})"
        
        # 5. Only links/media (no text)
        text_clean = tweet.text.replace("http", "").replace("www", "").strip()
        if len(text_clean) < 30:
            return False, "Brak treści (tylko linki/media)"
        
        return True, "OK - przechodzi do AI"
    
    async def verify(self, tweet: Tweet, username: str) -> VerificationResult:
        """
        Główna metoda weryfikacji.
        Najpierw szybkie filtry, potem AI.
        """
        
        # Szybkie filtry (cheap)
        passed_basic, reason = self._basic_filters(tweet)
        if not passed_basic:
            return VerificationResult(
                should_send=False,
                reason=reason,
                quality_score=0,
                category="filtered",
                is_original_content=False
            )
        
        # AI verification (expensive - only if passed basic)
        return await self._ai_verify(tweet, username)
    
    async def _ai_verify(self, tweet: Tweet, username: str) -> VerificationResult:
        """AI analiza jakości tweeta."""
        
        prompt = f"""Analyze this tweet and determine if it should be sent to Discord.

Tweet from @{username}:
"{tweet.text}"

Metrics: ❤️ {tweet.likes} | 🔁 {tweet.retweets} | 💬 {tweet.replies}

Evaluate:
1. Is this ORIGINAL content (not quote, not reply thread)?
2. Does it provide VALUE (insights, tips, analysis, news)?
3. Is it WELL-WRITTEN (clear, coherent, not shitposting)?
4. Is it RELEVANT (tech/business/crypto/AI, not personal life)?

CATEGORIES:
- "ai" - AI/ML, LLMs, automation
- "crypto" - crypto, blockchain, DeFi
- "business" - startups, marketing, sales
- "tech" - programming, tools, SaaS
- "productivity" - habits, workflows
- "filtered" - low quality, skip

RESPONSE FORMAT (JSON):
{{
  "should_send": true/false,
  "reason": "One sentence why",
  "quality_score": 0-10,
  "category": "category_name",
  "is_original_content": true/false
}}"""

        try:
            response = await ai_router.generate(
                prompt=prompt,
                task_type="analysis",
                temperature=0.2,
                max_tokens=500
            )
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON from markdown if present
            json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
            
            data = json.loads(response)
            
            return VerificationResult(
                should_send=data.get("should_send", False),
                reason=data.get("reason", "AI verification"),
                quality_score=data.get("quality_score", 0),
                category=data.get("category", "filtered"),
                is_original_content=data.get("is_original_content", False)
            )
            
        except Exception as e:
            logger.error(f"AI verification failed: {e}")
            # Fail safe - if AI fails, allow basic-filtered tweets
            return VerificationResult(
                should_send=True,  # Better to allow than block
                reason=f"AI error, basic filters passed: {e}",
                quality_score=5,
                category="unknown",
                is_original_content=True
            )


# Singleton
discord_verifier = DiscordVerifierAgent()
