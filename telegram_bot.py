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
        
        # Store builds awaiting requirements
        self.awaiting_requirements: Dict[str, Dict] = {}
        
        # Counters for each category (AI-001, CRYPTO-005, etc.)
        self.category_counters: Dict[str, int] = {}
        self.global_counter = 0
    
    def _generate_tweet_id(self, category: str) -> str:
        """Generate unique ID like AI-001, CRYPTO-005, etc."""
        category = category.upper()[:10]  # Max 10 chars
        
        # Increment counter for this category
        if category not in self.category_counters:
            self.category_counters[category] = 0
        self.category_counters[category] += 1
        
        # Also global counter for uniqueness
        self.global_counter += 1
        
        return f"{category}-{self.category_counters[category]:03d}"
    
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
        
        # Generate unique ID for this alert
        alert_id = self._generate_tweet_id(category)
        
        # Truncate tweet text
        display_text = tweet_text[:280] + "..." if len(tweet_text) > 280 else tweet_text
        reason_clean = reason[:60] + "..." if len(reason) > 60 else reason
        
        message = f"""🚨 [{alert_id}] URGENT {score}/10

👤 @{username} | 📊 {category.upper()}

💬 {display_text}

📝 {reason_clean}

Choose action ⬇️"""

        # Inline keyboard with action buttons
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "1️⃣ INTERESTING", "callback_data": f"INTERESTING:{alert_id}"},
                    {"text": "2️⃣ NOTHING", "callback_data": f"NOTHING:{alert_id}"},
                    {"text": "3️⃣ BUILD", "callback_data": f"BUILD:{alert_id}"}
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
                    
                    # Store pending tweet with alert_id as key
                    self.pending_tweets[alert_id] = {
                        "alert_id": alert_id,
                        "username": username,
                        "text": tweet_text,
                        "score": score,
                        "category": category,
                        "reason": reason,
                        "sent_at": datetime.now(),
                        "telegram_message_id": sent_message_id,
                        "status": "pending",
                        "original_tweet_id": tweet_id
                    }
                    
                    logger.info(f"📨 Telegram sent [{alert_id}] for @{username}")
                    return {"sent": True, "alert_id": alert_id, "message_id": sent_message_id, "cost": "$0.00"}
                else:
                    error = response.json().get("description", "Unknown error")
                    logger.error(f"Telegram send failed: {error}")
                    return {"sent": False, "error": error}
                    
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return {"sent": False, "error": str(e)}
    
    async def send_message(self, chat_id: str, text: str, reply_markup: dict = None) -> Dict:
        """Send a simple text message."""
        if not self.base_url:
            return {"sent": False, "error": "Not configured"}
        
        try:
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json=payload
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
                        "text": text[:200]  # Max 200 chars
                    }
                )
        except Exception as e:
            logger.error(f"Failed to answer callback: {e}")
    
    async def update_message(
        self,
        chat_id: int,
        message_id: int,
        action: str,
        result: Dict,
        alert_id: str = ""
    ):
        """Update message to show action taken."""
        if not self.base_url:
            return
        
        # Action emojis
        emoji = {"INTERESTING": "📌", "NOTHING": "🗑️", "BUILD": "🔨", "AWAITING_INPUT": "⏳"}.get(action, "✅")
        
        text = f"{emoji} [{alert_id}] {action}\n\n{result.get('message', 'Done!')}"
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/editMessageText",
                    json={
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "text": text
                    }
                )
        except Exception as e:
            logger.error(f"Failed to update message: {e}")
    
    async def request_build_requirements(self, alert_id: str, chat_id: int) -> Dict:
        """Ask user for additional requirements before building."""
        
        pending = self.pending_tweets.get(alert_id, {})
        
        # Store that we're awaiting requirements
        self.awaiting_requirements[alert_id] = {
            **pending,
            "chat_id": chat_id,
            "requested_at": datetime.now()
        }
        
        # Send requirements request
        message = f"""🔨 BUILD: [{alert_id}]

Original idea:
💬 {pending.get('text', '')[:200]}...

📝 ADD YOUR INPUT:
Reply with any tips, requirements, or info for Kimi to consider.

Examples of what you can write:
- "Use Qwen Coder instead of Claude to save money"
- "Focus on La Liga, not Premier League"
- "I want SMS alerts when bets win"
- "Skip the fancy UI, keep it simple"
- "Make it a Telegram bot, not web app"

Or reply "DEFAULT" to build as-is."""

        await self.send_message(chat_id, message)
        
        return {
            "success": True, 
            "message": f"Awaiting your requirements for [{alert_id}]. Reply with customizations or 'DEFAULT'"
        }
    
    async def process_reply(self, action: str, alert_id: str, user_text: str = None, chat_id: int = None) -> Dict:
        """Process user reply action."""
        
        # Check if this is a requirements reply for a build
        if alert_id in self.awaiting_requirements and user_text:
            # This is requirements input - trigger the actual build
            build_data = self.awaiting_requirements.pop(alert_id)
            
            requirements = user_text if user_text.upper() != "DEFAULT" else "None - build as described in tweet"
            
            # Trigger build with requirements
            try:
                from build_agent_enhanced import enhanced_build_agent
                
                # Enhance the tweet text with user requirements - Kimi will analyze BOTH
                enhanced_tweet = f"""ORIGINAL TWEET/IDEA:
{build_data.get('text', '')}

USER CUSTOMIZATION REQUIREMENTS (MUST IMPLEMENT):
{requirements}

INSTRUCTION FOR AI ARCHITECT:
Analyze BOTH the original tweet AND the user requirements above. 
Create a project plan that incorporates the user's specific customizations.
The user requirements override default choices (e.g., if user says "use Qwen", use Qwen not Claude).
Balance cost vs features based on user priorities stated above."""
                
                result = await enhanced_build_agent.build_project(
                    tweet_text=enhanced_tweet,
                    username=build_data.get("username", "unknown")
                )
                
                if result["success"]:
                    if alert_id in self.pending_tweets:
                        self.pending_tweets[alert_id]["status"] = "built"
                    
                    return {
                        "success": True,
                        "message": f"🔨 [{alert_id}] BUILD COMPLETE!\n\nProject: {result['project_name']}\nStack: {', '.join(result.get('tech_stack', [])[:3])}\n\nWith customizations:\n{requirements[:100]}..."
                    }
                else:
                    return {"success": False, "message": f"[{alert_id}] Build failed: {result.get('error', 'Unknown')}"}
            except Exception as e:
                return {"success": False, "message": f"[{alert_id}] Build error: {e}"}
        
        # Get pending tweet data
        pending = self.pending_tweets.get(alert_id, {})
        
        if action == "INTERESTING":
            # Send to Discord "Interesting" channel
            try:
                from discord_client import discord_client
                await discord_client.send_interesting(
                    username=pending.get("username", "unknown"),
                    tweet_text=pending.get("text", ""),
                    score=pending.get("score", 0),
                    reason=f"[{alert_id}] User marked as INTERESTING from Telegram"
                )
                
                if alert_id in self.pending_tweets:
                    self.pending_tweets[alert_id]["status"] = "interesting"
                
                return {"success": True, "message": f"Sent to Discord #interesting! [{alert_id}]"}
            except Exception as e:
                return {"success": False, "message": f"Discord error: {e}"}
        
        elif action == "NOTHING":
            # Just mark as filtered
            if alert_id in self.pending_tweets:
                self.pending_tweets[alert_id]["status"] = "filtered"
            
            return {"success": True, "message": f"Skipped [{alert_id}]. Tweet filtered."}
        
        elif action == "BUILD":
            # If we have chat_id, request requirements first
            if chat_id:
                return await self.request_build_requirements(alert_id, chat_id)
            
            # Otherwise try to build without requirements (legacy)
            tweet_text = pending.get("text", "")
            
            if not tweet_text:
                return {"success": False, "message": f"[{alert_id}] No tweet text found"}
            
            try:
                from build_agent_enhanced import enhanced_build_agent
                
                result = await enhanced_build_agent.build_project(
                    tweet_text=tweet_text,
                    username=pending.get("username", "unknown")
                )
                
                if result["success"]:
                    if alert_id in self.pending_tweets:
                        self.pending_tweets[alert_id]["status"] = "built"
                    
                    return {
                        "success": True,
                        "message": f"[{alert_id}] BUILD STARTED!\nProject: {result['project_name'][:30]}..."
                    }
                else:
                    return {"success": False, "message": f"[{alert_id}] Build failed: {result.get('error', 'Unknown')}"}
            except Exception as e:
                return {"success": False, "message": f"[{alert_id}] Build error: {e}"}
        
        return {"success": False, "message": f"Unknown action: {action}"}
    
    def get_pending_count(self) -> int:
        """Get count of pending tweets."""
        return len([t for t in self.pending_tweets.values() if t.get("status") == "pending"])
    
    def get_pending_list(self) -> list:
        """Get list of pending tweets with their IDs."""
        return [
            {
                "id": alert_id,
                "username": data["username"],
                "category": data["category"],
                "score": data["score"],
                "status": data["status"],
                "sent_at": data["sent_at"].isoformat()
            }
            for alert_id, data in self.pending_tweets.items()
            if data.get("status") == "pending"
        ]
    
    def is_awaiting_requirements(self, alert_id: str) -> bool:
        """Check if we're waiting for requirements for this alert."""
        return alert_id in self.awaiting_requirements
    
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
