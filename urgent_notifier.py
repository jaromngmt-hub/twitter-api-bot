"""Urgent notification system for high-value tweets (score 9-10).

Sends critical tweets directly to phone via:
- SMS (Twilio)
- WhatsApp (Twilio/WhatsApp Business)
- Telegram Bot
- Pushover (push notifications)
"""

import asyncio
from typing import Optional

import httpx
from loguru import logger

from config import settings
from models import Tweet


class UrgentNotifier:
    """
    Sends urgent notifications for critical tweets (score 9-10).
    
    Ensures you never miss life-changing alpha!
    """
    
    def __init__(self):
        self.enabled = settings.URGENT_NOTIFICATIONS_ENABLED
        self.min_score = settings.URGENT_MIN_SCORE  # Usually 9
        
        # Twilio (SMS/WhatsApp)
        self.twilio_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_token = settings.TWILIO_AUTH_TOKEN
        self.twilio_from = settings.TWILIO_PHONE_NUMBER
        self.your_phone = settings.YOUR_PHONE_NUMBER
        
        # Telegram
        self.telegram_bot_token = settings.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = settings.TELEGRAM_CHAT_ID
        
        # Pushover
        self.pushover_token = settings.PUSHOVER_APP_TOKEN
        self.pushover_user = settings.PUSHOVER_USER_KEY
        
        # HTTP client
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(30))
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def send_urgent_notification(
        self,
        username: str,
        tweet: Tweet,
        rating: dict
    ) -> dict:
        """
        Send urgent notification for high-value tweet.
        
        Tries multiple channels in order of reliability.
        """
        if not self.enabled:
            return {"sent": False, "reason": "Notifications disabled"}
        
        score = rating.get("score", 0)
        if score < self.min_score:
            return {"sent": False, "reason": f"Score {score} below threshold {self.min_score}"}
        
        results = {}
        
        # Try SMS first (most reliable)
        if self.twilio_sid and self.your_phone:
            try:
                result = await self._send_sms(username, tweet, rating)
                results["sms"] = result
                if result.get("sent"):
                    logger.info(f"📱 SMS sent for urgent tweet from @{username}")
            except Exception as e:
                logger.error(f"SMS failed: {e}")
                results["sms"] = {"sent": False, "error": str(e)}
        
        # Try WhatsApp
        if self.twilio_sid and self.your_phone:
            try:
                result = await self._send_whatsapp(username, tweet, rating)
                results["whatsapp"] = result
                if result.get("sent"):
                    logger.info(f"💬 WhatsApp sent for urgent tweet from @{username}")
            except Exception as e:
                logger.error(f"WhatsApp failed: {e}")
                results["whatsapp"] = {"sent": False, "error": str(e)}
        
        # Try Telegram
        if self.telegram_bot_token:
            try:
                result = await self._send_telegram(username, tweet, rating)
                results["telegram"] = result
                if result.get("sent"):
                    logger.info(f"📨 Telegram sent for urgent tweet from @{username}")
            except Exception as e:
                logger.error(f"Telegram failed: {e}")
                results["telegram"] = {"sent": False, "error": str(e)}
        
        # Try Pushover
        if self.pushover_token:
            try:
                result = await self._send_pushover(username, tweet, rating)
                results["pushover"] = result
                if result.get("sent"):
                    logger.info(f"🔔 Pushover sent for urgent tweet from @{username}")
            except Exception as e:
                logger.error(f"Pushover failed: {e}")
                results["pushover"] = {"sent": False, "error": str(e)}
        
        # Return summary
        any_sent = any(r.get("sent") for r in results.values())
        return {
            "sent": any_sent,
            "channels": results,
            "score": score,
            "username": username
        }
    
    async def _send_sms(self, username: str, tweet: Tweet, rating: dict) -> dict:
        """Send SMS via Twilio."""
        if not all([self.twilio_sid, self.twilio_token, self.twilio_from, self.your_phone]):
            return {"sent": False, "error": "Twilio not configured"}
        
        score = rating.get("score", 0)
        summary = rating.get("summary", tweet.text[:100])
        category = rating.get("category", "unknown")
        
        # Short message for SMS (160 char limit)
        message = f"""🚨 URGENT TWEET {score}/10

@{username}: {summary[:80]}...

Category: {category}
Open: https://twitter.com/{username}
"""
        
        response = await self.client.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json",
            auth=(self.twilio_sid, self.twilio_token),
            data={
                "From": self.twilio_from,
                "To": self.your_phone,
                "Body": message[:1600]  # Twilio limit
            }
        )
        
        if response.status_code == 201:
            return {"sent": True, "sid": response.json().get("sid")}
        else:
            return {"sent": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    async def _send_whatsapp(self, username: str, tweet: Tweet, rating: dict) -> dict:
        """Send WhatsApp message via Twilio with action options."""
        if not all([self.twilio_sid, self.twilio_token, self.your_phone]):
            return {"sent": False, "error": "Twilio not configured"}
        
        score = rating.get("score", 0)
        summary = rating.get("summary", tweet.text[:200])
        category = rating.get("category", "unknown")
        reason = rating.get("reason", "High value content")
        
        # Richer message for WhatsApp with action options
        message = f"""🚨 *URGENT TWEET ALERT* 🚨

*Score:* {score}/10 ⭐
*From:* @{username}
*Category:* {category.upper()}

*Content:*
{summary}

*Why urgent:*
{reason}

🔗 Open: https://twitter.com/{username}/status/{tweet.id}

━━━━━━━━━━━━━━━━━━━━━━
*Reply with:*
1️⃣ *INTERESTING* → Share to Discord
2️⃣ *NOTHING* → Skip this  
3️⃣ *BUILD* → Create project
━━━━━━━━━━━━━━━━━━━━━━

💡 *Quick reply:*
Type: 1 / 2 / 3
Or: I / N / B"""
        
        # Use Twilio WhatsApp sandbox number (NOT your regular Twilio number)
        # This is the number you sent "join" message to
        from_number = "whatsapp:+14155238886"
        
        to_number = self.your_phone
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        
        response = await self.client.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json",
            auth=(self.twilio_sid, self.twilio_token),
            data={
                "From": from_number,
                "To": to_number,
                "Body": message
            }
        )
        
        if response.status_code == 201:
            return {"sent": True, "sid": response.json().get("sid")}
        else:
            return {"sent": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    async def _send_whatsapp_raw(self, to: str, message: str) -> dict:
        """Send raw WhatsApp message (used by Build Agent)."""
        if not all([self.twilio_sid, self.twilio_token]):
            return {"sent": False, "error": "Twilio not configured"}
        
        from_number = "whatsapp:+14155238886"
        
        to_number = to
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        
        response = await self.client.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json",
            auth=(self.twilio_sid, self.twilio_token),
            data={
                "From": from_number,
                "To": to_number,
                "Body": message
            }
        )
        
        if response.status_code == 201:
            return {"sent": True, "sid": response.json().get("sid")}
        else:
            return {"sent": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    async def _send_telegram(self, username: str, tweet: Tweet, rating: dict) -> dict:
        """Send Telegram message."""
        if not all([self.telegram_bot_token, self.telegram_chat_id]):
            return {"sent": False, "error": "Telegram not configured"}
        
        score = rating.get("score", 0)
        category = rating.get("category", "unknown")
        summary = rating.get("summary", tweet.text[:300])
        reason = rating.get("reason", "")
        
        # Emoji based on score
        emoji = "🚨" if score >= 10 else "⭐" if score == 9 else "💎"
        
        message = f"""{emoji} <b>URGENT TWEET {score}/10</b> {emoji}

<b>From:</b> @{username}
<b>Category:</b> {category.upper()}

<b>Content:</b>
{summary}

<b>AI Reasoning:</b>
{reason}

<a href="https://twitter.com/{username}/status/{tweet.id}">🔗 View on Twitter</a>

<i>Sent by Twitter Monitor Bot</i>
"""
        
        response = await self.client.post(
            f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage",
            json={
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }
        )
        
        if response.status_code == 200:
            return {"sent": True}
        else:
            return {"sent": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    async def _send_pushover(self, username: str, tweet: Tweet, rating: dict) -> dict:
        """Send Pushover notification."""
        if not all([self.pushover_token, self.pushover_user]):
            return {"sent": False, "error": "Pushover not configured"}
        
        score = rating.get("score", 0)
        category = rating.get("category", "unknown")
        summary = rating.get("summary", tweet.text[:100])
        
        # Priority: 2 = Emergency (bypasses quiet hours)
        priority = 2 if score >= 10 else 1 if score == 9 else 0
        
        response = await self.client.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": self.pushover_token,
                "user": self.pushover_user,
                "title": f"🚨 URGENT: @{username} ({score}/10)",
                "message": f"{category.upper()}: {summary[:300]}...",
                "url": f"https://twitter.com/{username}/status/{tweet.id}",
                "url_title": "View Tweet",
                "priority": priority,
                "sound": "siren" if score >= 10 else "pushover"
            }
        )
        
        if response.status_code == 200:
            return {"sent": True}
        else:
            return {"sent": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    def is_configured(self) -> bool:
        """Check if any notification channel is configured."""
        return any([
            self.twilio_sid and self.your_phone,
            self.telegram_bot_token,
            self.pushover_token
        ])
