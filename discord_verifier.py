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
    market_potential: str = "none"  # high/medium/low/none
    pioneer_opportunity: bool = False
    build_alternative: Optional[str] = None
    

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
    
    MIN_LENGTH = 30  # Min długość tweeta (niżej - nowe tweety też OK)
    # MIN_LIKES usunięte - nowe wartościowe tweety mogą mieć mało likes
    
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
        
        # 3. Too short (but allow if high quality content)
        if len(tweet.text) < self.MIN_LENGTH:
            return False, f"Za krótki ({len(tweet.text)} znaków)"
        
        # 4. Only links with NO context (like just "https://..." without explanation)
        # Allow links WITH context (explanation of what it is)
        words = tweet.text.split()
        link_count = sum(1 for w in words if w.startswith('http') or 't.co' in w)
        text_words = [w for w in words if not w.startswith('http') and 't.co' not in w]
        
        if link_count > 0 and len(text_words) < 5:
            # Just a link with 0-4 words of context = spam
            return False, "Tylko link bez opisu (spam)"
        
        # 5. Allow all other tweets - let AI decide
        
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
        
        prompt = f"""You are a content curator. Analyze this tweet CAREFULLY.

Tweet from @{username}:
"{tweet.text}"

Metrics: ❤️ {tweet.likes} | 🔁 {tweet.retweets} | 💬 {tweet.replies}

IMPORTANT: Many accounts post VALUABLE insights, tips, strategies, analysis. 
DON'T miss them! Be GENEROUS with approval.

APPROVE (should_send: true) if tweet is:
✓ Original insight, lesson learned, strategy
✓ Tutorial, how-to, guide, playbook
✓ Analysis, breakdown, case study
✓ Useful tool, resource, recommendation
✓ Industry news with context
✓ Thought-provoking question/discussion
✓ Personal experience with lesson
✓ Data, statistics, research findings
✓ **Early product idea with market validation potential**

PIONEER OPPORTUNITY - Give HIGHER score if:
🔥 Is this something people would WANT TO USE or PAY FOR?
🔥 Even if incomplete, can we build an alternative/improved version?
🔥 Is this validating market demand ("thinking to build", "would you use")?
🔥 Can we be FIRST to build what they're discussing?

⚠️ CRITICAL: Read the tweet CAREFULLY!
- Don't confuse metaphors with actual products
- "Landing page as commitment device" = METHAPHOR, not a product idea
- Look for ACTUAL tech/blockchain/AI mentions
- Understand the DOMAIN (Solana, AI agents, etc.)

REJECT (should_send: false) only if:
✗ Pure retweet (RT @user)
✗ Simple reply (@user thanks/cool/agreed)
✗ Personal life update (food, travel, mood)
✗ Meme/shitpost without value
✗ Just a link with zero context
✗ Duplicate/spam content

CATEGORIES:
- "ai" - AI/ML, LLMs, ChatGPT, automation, prompts
- "crypto" - crypto, blockchain, DeFi, trading, Web3
- "business" - startups, marketing, sales, growth, monetization
- "tech" - programming, SaaS, dev tools, open source
- "productivity" - habits, systems, workflows, focus
- "content" - writing, social media, audience building
- "filtered" - reject only if truly worthless

BE GENEROUS! Better to approve good content than miss it!

RESPONSE FORMAT (JSON):
{{
  "should_send": true/false,
  "reason": "Why - what value does it provide?",
  "quality_score": 0-10,
  "category": "category_name",
  "is_original_content": true/false,
  "market_potential": "high/medium/low/none",
  "pioneer_opportunity": true/false,
  "build_alternative": "Based on ACTUAL tweet content - what could we build? Be specific to the domain mentioned (Solana, AI, etc.). NULL if no clear opportunity."
}}"""

        try:
            response = await ai_router.generate(
                prompt=prompt,
                task_type="analysis",  # Używa Kimi K2.5 (dodane do defaults!)
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
                is_original_content=data.get("is_original_content", False),
                market_potential=data.get("market_potential", "none"),
                pioneer_opportunity=data.get("pioneer_opportunity", False),
                build_alternative=data.get("build_alternative")
            )
            
        except Exception as e:
            logger.error(f"AI verification failed: {e}")
            # Fail safe - if AI fails, allow basic-filtered tweets
            return VerificationResult(
                should_send=True,  # Better to allow than block
                reason=f"AI error, basic filters passed: {e}",
                quality_score=5,
                category="unknown",
                is_original_content=True,
                market_potential="unknown",
                pioneer_opportunity=False,
                build_alternative=None
            )


# Singleton
discord_verifier = DiscordVerifierAgent()
