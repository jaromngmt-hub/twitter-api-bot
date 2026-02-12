"""Action handler for AI-detected opportunities.

This module handles special actions detected by AI analysis:
- build_bot: Automatically build/deploy bots
- follow_user: Follow interesting accounts
- store_info: Save valuable information
- alert_admin: Send urgent alerts
"""

import json
from datetime import datetime
from typing import Dict, Any

from loguru import logger

from config import settings


class ActionHandler:
    """Handles AI-detected actions and opportunities."""
    
    def __init__(self):
        self.action_log = []
    
    async def handle(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an AI-detected action.
        
        Args:
            action: The action type (build_bot, follow_user, etc.)
            context: Context including username, tweet, rating, etc.
        
        Returns:
            Result of the action
        """
        handler_map = {
            "build_bot": self._handle_build_bot,
            "follow_user": self._handle_follow_user,
            "store_info": self._handle_store_info,
            "alert_admin": self._handle_alert_admin,
            "highlight": self._handle_highlight,
            "research": self._handle_research,
        }
        
        handler = handler_map.get(action.lower())
        if not handler:
            logger.warning(f"Unknown action: {action}")
            return {"success": False, "error": "Unknown action"}
        
        try:
            result = await handler(context)
            self._log_action(action, context, result)
            return result
        except Exception as e:
            logger.error(f"Action handler failed for {action}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_build_bot(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'build_bot' action - Deploy a new bot automatically.
        
        This is triggered when AI detects a tweet about a bot/tool
        that should be built or deployed.
        """
        username = context.get("username", "unknown")
        tweet_text = context.get("tweet", {}).get("text", "")
        rating = context.get("rating", {})
        
        logger.info(f"🤖 BUILD_BOT triggered by @{username}")
        logger.info(f"   Reason: {rating.get('reason', 'No reason')}")
        logger.info(f"   Tweet: {tweet_text[:150]}...")
        
        # TODO: Implement bot building logic
        # Ideas:
        # - Parse tweet for bot description
        # - Use AI to generate bot code
        # - Deploy to Render/Railway automatically
        # - Send deployed URL back to Discord
        
        # For now, just log and alert
        return {
            "success": True,
            "action": "build_bot",
            "status": "logged_for_review",
            "message": f"Bot build request from @{username} logged",
            "next_steps": [
                "Review tweet content",
                "Generate bot specification",
                "Deploy to cloud",
                "Send confirmation to Discord"
            ]
        }
    
    async def _handle_follow_user(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'follow_user' action - Follow an interesting account.
        
        Triggered when AI detects a high-value user that should be monitored.
        """
        username = context.get("username", "unknown")
        rating = context.get("rating", {})
        
        logger.info(f"👤 FOLLOW_USER triggered for @{username}")
        logger.info(f"   Score: {rating.get('score', 0)}/10")
        
        # TODO: Implement auto-follow
        # This requires Twitter API v2 with write permissions
        # For now, add to a "suggested follows" list
        
        return {
            "success": True,
            "action": "follow_user",
            "status": "suggested",
            "username": username,
            "message": f"Added @{username} to suggested follows"
        }
    
    async def _handle_store_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'store_info' action - Save valuable information.
        
        Store tweets containing alpha, insights, or useful data.
        """
        username = context.get("username", "unknown")
        tweet = context.get("tweet", {})
        rating = context.get("rating", {})
        
        # Create structured data
        stored_data = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "tweet_id": tweet.get("id"),
            "text": tweet.get("text"),
            "score": rating.get("score"),
            "category": rating.get("category"),
            "summary": rating.get("summary"),
            "action": "stored"
        }
        
        # TODO: Store in database or vector DB for search
        logger.info(f"💾 STORED info from @{username}: {stored_data['summary'][:80]}...")
        
        return {
            "success": True,
            "action": "store_info",
            "data": stored_data
        }
    
    async def _handle_alert_admin(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'alert_admin' action - Send urgent alert.
        
        For critical opportunities or breaking news.
        """
        username = context.get("username", "unknown")
        tweet = context.get("tweet", {})
        rating = context.get("rating", {})
        
        logger.info(f"🚨 URGENT ALERT from @{username}!")
        logger.info(f"   Score: {rating.get('score', 0)}/10")
        logger.info(f"   Category: {rating.get('category', 'unknown')}")
        
        # TODO: Send SMS/email/push notification
        # For now, high-priority Discord message
        
        return {
            "success": True,
            "action": "alert_admin",
            "priority": "urgent",
            "message": f"Critical alert from @{username}"
        }
    
    async def _handle_highlight(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'highlight' action - Mark as important.
        
        Default action for high-value tweets (7-10 score).
        """
        return {
            "success": True,
            "action": "highlight",
            "message": "Tweet highlighted for premium channel"
        }
    
    async def _handle_research(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle 'research' action - Deep dive needed.
        
        When AI detects something worth investigating further.
        """
        username = context.get("username", "unknown")
        tweet_text = context.get("tweet", {}).get("text", "")
        
        logger.info(f"🔬 RESEARCH needed on @{username}")
        
        # TODO: Trigger research pipeline
        # - Scrape user's history
        # - Analyze patterns
        # - Generate report
        
        return {
            "success": True,
            "action": "research",
            "status": "queued",
            "message": f"Research queued for @{username}"
        }
    
    def _log_action(self, action: str, context: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Log the action for audit trail."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "username": context.get("username"),
            "tweet_id": context.get("tweet", {}).get("id"),
            "result": result.get("success"),
            "status": result.get("status")
        }
        self.action_log.append(log_entry)
        
        # Keep only last 1000 actions
        if len(self.action_log) > 1000:
            self.action_log = self.action_log[-1000:]
    
    def get_action_stats(self) -> Dict[str, Any]:
        """Get statistics about handled actions."""
        stats = {}
        for entry in self.action_log:
            action = entry["action"]
            if action not in stats:
                stats[action] = {"total": 0, "success": 0, "failed": 0}
            stats[action]["total"] += 1
            if entry["result"]:
                stats[action]["success"] += 1
            else:
                stats[action]["failed"] += 1
        
        return {
            "total_actions": len(self.action_log),
            "by_action": stats
        }
