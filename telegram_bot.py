"""Telegram Bot Integration for Twitter Monitor.

FREE alternative to WhatsApp ($0.04/msg).
Handles urgent notifications and user replies.
"""

import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger

from config import settings


class TelegramBot:
    """Telegram bot for urgent notifications."""
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.USE_TELEGRAM and bool(self.token and self.chat_id)
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else None
        
        # Store pending tweets awaiting user action
        self.pending_tweets: Dict[str, Dict] = {}
    
    async def send_urgent_tweet(
        self,
        username: str,
        tweet_text: str,
        score: int,
        category: str,
        reason: str,
        tweet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send urgent tweet notification with action buttons."""
        
        if not self.enabled:
            return {"sent": False, "error": "Telegram not configured"}
        
        # Truncate tweet text (no formatting to avoid parse errors)
        display_text = tweet_text[:300] + "..." if len(tweet_text) > 300 else tweet_text
        reason_clean = reason[:80] + "..." if len(reason) > 80 else reason
        
        message = f"""🚨 URGENT TWEET {score}/10

👤 @{username}
📊 Category: {category.upper()}

💬 Tweet:
{display_text}

📝 Why: {reason_clean}

Reply with buttons below ⬇️"""

        # Inline keyboard with action buttons
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "1️⃣ INTERESTING", "callback_data": f"INTERESTING:{tweet_id or 'unknown'}"},
                    {"text": "2️⃣ NOTHING", "callback_data": f"NOTHING:{tweet_id or 'unknown'}"},
                    {"text": "3️⃣ BUILD", "callback_data": f"BUILD:{tweet_id or 'unknown'}"}
                ]
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "reply_markup": keyboard,
                        "disable_web_page_preview": True
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    sent_message_id = data["result"]["message_id"]
                    
                    # Store pending tweet
                    if tweet_id:
                        self.pending_tweets[tweet_id] = {
                            "username": username,
                            "text": tweet_text,
                            "score": score,
                            "category": category,
                            "sent_at": datetime.now(),
                            "telegram_message_id": sent_message_id,
                            "status": "pending"
                        }
                    
                    logger.info(f"📨 Telegram sent for @{username} (message_id: {sent_message_id})")
                    return {"sent": True, "message_id": sent_message_id, "cost": "$0.00"}
                else:
                    error = response.json().get("description", "Unknown error")
                    logger.error(f"Telegram send failed: {error}")
                    return {"sent": False, "error": error}
                    
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return {"sent": False, "error": str(e)}
    
    async def send_message(self, chat_id: str, text: str) -> Dict:
        """Send a simple text message."""
        if not self.base_url:
            return {"sent": False, "error": "Not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "Markdown"
                    }
                )
                return {"sent": response.status_code == 200}
        except Exception as e:
            return {"sent": False, "error": str(e)}
    
    async def answer_callback(self, callback_id: str, text: str):
        """Answer a callback query (button click)."""
        if not self.base_url:
            return
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/answerCallbackQuery",
                    json={
                        "callback_query_id": callback_id,
                        "text": text
                    }
                )
        except Exception as e:
            logger.error(f"Failed to answer callback: {e}")
    
    async def update_message(
        self,
        chat_id: int,
        message_id: int,
        action: str,
        result: Dict
    ):
        """Update message to show action taken."""
        if not self.base_url:
            return
        
        # Action emojis
        emoji = {"INTERESTING": "📌", "NOTHING": "🗑️", "BUILD": "🔨"}.get(action, "✅")
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/editMessageText",
                    json={
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "text": f"{emoji} *Action Taken: {action}*\n\n{result.get('message', 'Processing...')}",
                        "parse_mode": "Markdown"
                    }
                )
        except Exception as e:
            logger.error(f"Failed to update message: {e}")
    
    async def process_reply(self, action: str, tweet_id: Optional[str] = None) -> Dict:
        """Process user reply action."""
        
        if action == "INTERESTING":
            # Get pending tweet data
            pending = self.pending_tweets.get(tweet_id, {})
            
            # Send to Discord "Interesting" channel
            try:
                from discord_client import discord_client
                await discord_client.send_interesting(
                    username=pending.get("username", "unknown"),
                    tweet_text=pending.get("text", ""),
                    score=pending.get("score", 0),
                    reason="User marked as INTERESTING from Telegram"
                )
                
                if tweet_id:
                    self.pending_tweets[tweet_id]["status"] = "interesting"
                
                return {"success": True, "message": "Sent to Discord #interesting! ✅"}
            except Exception as e:
                return {"success": False, "message": f"Discord error: {e}"}
        
        elif action == "NOTHING":
            # Just mark as filtered
            if tweet_id:
                self.pending_tweets[tweet_id]["status"] = "filtered"
            
            return {"success": True, "message": "Skipped. Tweet filtered. 🗑️"}
        
        elif action == "BUILD":
            # Trigger build process
            pending = self.pending_tweets.get(tweet_id, {})
            tweet_text = pending.get("text", "")
            
            if not tweet_text:
                return {"success": False, "message": "No tweet text found"}
            
            try:
                from build_agent_enhanced import enhanced_build_agent
                
                result = await enhanced_build_agent.build_project(
                    tweet=tweet_text,
                    username=pending.get("username", "unknown")
                )
                
                if result["success"]:
                    if tweet_id:
                        self.pending_tweets[tweet_id]["status"] = "built"
                    
                    return {
                        "success": True,
                        "message": f"🔨 BUILD STARTED!\n\nProject: {result['project_name']}\nRepo: {result.get('repo_url', 'N/A')[:50]}..."
                    }
                else:
                    return {"success": False, "message": f"Build failed: {result.get('error', 'Unknown')}"}
            except Exception as e:
                return {"success": False, "message": f"Build error: {e}"}
        
        return {"success": False, "message": f"Unknown action: {action}"}
    
    def get_pending_count(self) -> int:
        """Get count of pending tweets."""
        return len([t for t in self.pending_tweets.values() if t.get("status") == "pending"])
    
    async def set_webhook(self, webhook_url: str) -> Dict:
        """Set webhook URL for receiving updates."""
        if not self.base_url:
            return {"success": False, "error": "Not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/setWebhook",
                    json={"url": webhook_url}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return {"success": True, "message": "Webhook set!"}
                    else:
                        return {"success": False, "error": data.get("description", "Unknown")}
                else:
                    return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance
telegram_bot = TelegramBot()
