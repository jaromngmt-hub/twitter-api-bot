#!/usr/bin/env python3
"""Handle WhatsApp replies for tweet action workflow.

User receives urgent tweet via WhatsApp and can reply:
- "INTERESTING" or "1" → Send to Discord INTERESTING channel
- "NOTHING" or "NO" or "2" → Mark as filtered, log for learning
- "BUILD" or "3" → Trigger Build Agent (Kimi + Qwen) to create project
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any

from loguru import logger

from config import settings
from database import db
from discord_client import DiscordClient
from build_agent_enhanced import enhanced_build_agent
from urgent_notifier import UrgentNotifier
from models import Tweet


class WhatsAppActionHandler:
    """
    Process user replies to urgent tweet notifications.
    
    Workflow:
    1. User gets WhatsApp: "🚨 URGENT TWEET..."
    2. User replies with action
    3. This handler processes the reply
    4. Executes the requested action
    """
    
    def __init__(self):
        self.pending_tweets: Dict[str, Dict[str, Any]] = {}  # phone -> tweet data
        self.discord = DiscordClient()
    
    def store_pending_tweet(self, phone: str, username: str, tweet: Tweet, rating: dict):
        """Store tweet info while waiting for user reply."""
        self.pending_tweets[phone] = {
            "username": username,
            "tweet": tweet,
            "rating": rating,
            "sent_at": datetime.now(),
            "status": "pending"
        }
        logger.info(f"Stored pending tweet for {phone}: @{username}")
    
    async def process_reply(self, phone: str, reply_text: str) -> str:
        """
        Process user's WhatsApp reply.
        
        Returns confirmation message to send back.
        """
        reply = reply_text.strip().upper()
        
        # Check if we have a pending tweet for this phone
        if phone not in self.pending_tweets:
            return "❌ No pending tweet found. You may have already responded or the tweet expired."
        
        pending = self.pending_tweets[phone]
        username = pending["username"]
        tweet = pending["tweet"]
        rating = pending["rating"]
        
        # Parse action from reply
        action = self._parse_action(reply)
        
        if action == "INTERESTING":
            return await self._handle_interesting(phone, username, tweet, rating)
        
        elif action == "NOTHING":
            return await self._handle_nothing(phone, username, tweet, rating)
        
        elif action == "BUILD":
            return await self._handle_build(phone, username, tweet, rating)
        
        else:
            # Unknown action - ask again
            return """❓ Unknown reply.

Please respond with:
1️⃣ *INTERESTING* - Send to Discord
2️⃣ *NOTHING* - Filter this tweet  
3️⃣ *BUILD* - Create project from this idea"""
    
    def _parse_action(self, reply: str) -> str:
        """Parse action from user reply."""
        reply = reply.strip().upper()
        
        # INTERESTING variants
        if any(x in reply for x in ["INTERESTING", "YES", "SEND", "1", "DISCORD"]):
            return "INTERESTING"
        
        # NOTHING variants  
        if any(x in reply for x in ["NOTHING", "NO", "SKIP", "IGNORE", "2", "BAD", "TRASH"]):
            return "NOTHING"
        
        # BUILD variants
        if any(x in reply for x in ["BUILD", "CREATE", "MAKE", "PROJECT", "3", "REPO"]):
            return "BUILD"
        
        return "UNKNOWN"
    
    async def _handle_interesting(
        self, 
        phone: str, 
        username: str, 
        tweet: Tweet, 
        rating: dict
    ) -> str:
        """Send tweet to INTERESTING Discord channel."""
        webhook = settings.DISCORD_WEBHOOK_INTERESTING
        
        if not webhook:
            logger.error("INTERESTING webhook not configured")
            return "❌ INTERESTING channel not configured. Please add DISCORD_WEBHOOK_INTERESTING env var."
        
        try:
            async with self.discord:
                success = await self.discord.send_tweet(webhook, username, tweet)
            
            if success:
                # Log to database
                db.log_user_action(
                    phone=phone,
                    action="INTERESTING",
                    username=username,
                    tweet_id=tweet.id,
                    tweet_text=tweet.text[:200]
                )
                
                # Remove from pending
                del self.pending_tweets[phone]
                
                return f"✅ Sent to INTERESTING channel!\n\n@{username}'s tweet has been shared."
            else:
                return "❌ Failed to send to Discord. Please try again."
                
        except Exception as e:
            logger.error(f"Error sending to INTERESTING: {e}")
            return f"❌ Error: {str(e)}"
    
    async def _handle_nothing(
        self, 
        phone: str, 
        username: str, 
        tweet: Tweet, 
        rating: dict
    ) -> str:
        """Mark tweet as filtered - AI thought it was urgent but user disagrees."""
        # Log for AI learning
        db.log_user_action(
            phone=phone,
            action="FILTERED",
            username=username,
            tweet_id=tweet.id,
            tweet_text=tweet.text[:200],
            ai_score=rating.get("score", 0),
            reason="User marked as not interesting"
        )
        
        # Update AI model feedback (future enhancement)
        # This helps the AI learn what the user actually finds valuable
        
        # Remove from pending
        del self.pending_tweets[phone]
        
        logger.info(f"User {phone} filtered tweet from @{username}")
        
        return "✅ Noted. I'll learn from this and improve my scoring."
    
    async def _handle_build(
        self, 
        phone: str, 
        username: str, 
        tweet: Tweet, 
        rating: dict
    ) -> str:
        """
        Trigger Enhanced Build Agent (Kimi + Qwen) to create project from tweet.
        
        Pipeline:
        1. 🧠 Kimi K2 - Analyze & Plan
        2. 💻 Qwen Coder - Build & Implement
        3. 🔨 GitHub - Create private repo
        """
        
        # Send initial acknowledgment via WhatsApp
        notifier = UrgentNotifier()
        await notifier._send_whatsapp_raw(
            to=settings.YOUR_PHONE_NUMBER,
            message=f"🔨 *BUILD STARTED*\n\nTweet from @{username}:\n{tweet.text[:200]}...\n\n🧠 Kimi K2: Analyzing...\n💻 Qwen Coder: Ready to build\n\nThis takes ~2-3 minutes. I'll update you on progress!"
        )
        
        try:
            # Run full build pipeline with Kimi + Qwen
            logger.info(f"Starting BUILD for @{username} with Kimi+Qwen")
            
            result = await enhanced_build_agent.build_project(
                tweet_text=tweet.text,
                username=username
            )
            
            if result["success"]:
                # Build completed successfully!
                project_name = result["project_name"]
                github_url = f"https://github.com/{settings.GITHUB_USERNAME}/{project_name}"
                
                # ALSO send original tweet to INTERESTING channel
                webhook = settings.DISCORD_WEBHOOK_INTERESTING
                if webhook:
                    try:
                        async with self.discord:
                            await self.discord.send_tweet(
                                webhook, 
                                username, 
                                tweet,
                                note=f"🚀 Built into project: [{project_name}]({github_url})"
                            )
                        logger.info(f"Sent built tweet to INTERESTING channel: {project_name}")
                    except Exception as e:
                        logger.error(f"Failed to send to INTERESTING: {e}")
                
                # Send success message with repo link
                success_msg = f"""✅ *BUILD COMPLETE!*

📁 Project: *{project_name}*
🧠 Analyzed by: Kimi K2
💻 Built by: Qwen Coder
📊 Stats:
• {result['stats']['files_generated']} files
• {result['stats']['tests_generated']} tests
• Code quality: {result['stats']['review_score']}/10
• Est. time: {result['stats']['estimated_hours']} hours

🔗 *GitHub Repo (Private):*
{github_url}

📨 Also sent to INTERESTING channel!

🚀 Next steps:
{chr(10).join(result['next_steps'][:3])}

Built with 🤖 Kimi + Qwen (40x cheaper than GPT-4o!)"""
                
                await notifier._send_whatsapp_raw(
                    to=settings.YOUR_PHONE_NUMBER,
                    message=success_msg
                )
                
                # Log success
                db.log_user_action(
                    phone=phone,
                    action="BUILD_COMPLETED",
                    username=username,
                    tweet_id=tweet.id,
                    project_name=project_name,
                    reason=f"Kimi+Qwen build successful. Score: {result['stats']['review_score']}/10"
                )
                
            else:
                # Build failed
                error_msg = f"""❌ *BUILD FAILED*

Error: {result.get('error', 'Unknown error')}

The tweet might not contain a clear project idea, or there was a technical issue.

Try replying BUILD to a different tweet!"""
                
                await notifier._send_whatsapp_raw(
                    to=settings.YOUR_PHONE_NUMBER,
                    message=error_msg
                )
            
            # Remove from pending
            del self.pending_tweets[phone]
            
            return "Build process completed! Check WhatsApp for details."
            
        except Exception as e:
            logger.error(f"Build failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            await notifier._send_whatsapp_raw(
                to=settings.YOUR_PHONE_NUMBER,
                message=f"❌ *BUILD ERROR*\n\nSomething went wrong:\n{str(e)[:200]}\n\nPlease try again with a different tweet."
            )
            
            return f"❌ Build failed: {str(e)[:100]}"
    
    def get_pending_count(self) -> int:
        """Get number of pending tweets awaiting user response."""
        return len(self.pending_tweets)
    
    def cleanup_expired(self, max_age_minutes: int = 60):
        """Remove expired pending tweets."""
        now = datetime.now()
        expired = []
        
        for phone, data in self.pending_tweets.items():
            age = (now - data["sent_at"]).total_seconds() / 60
            if age > max_age_minutes:
                expired.append(phone)
        
        for phone in expired:
            del self.pending_tweets[phone]
            logger.info(f"Cleaned up expired pending tweet for {phone}")


# Singleton
whatsapp_handler = WhatsAppActionHandler()
