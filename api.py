"""FastAPI backend for Twitter Monitor Bot web interface."""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

from config import settings
from database import db
from scheduler import Scheduler
from twitter_client import TwitterClient
from loguru import logger

# Global scheduler instance
scheduler: Optional[Scheduler] = None


class ChannelCreate(BaseModel):
    name: str
    webhook_url: str


class UserCreate(BaseModel):
    username: str
    channel_name: str


class UserResponse(BaseModel):
    id: int
    username: str
    channel_name: str
    last_tweet_id: Optional[str]
    is_active: bool
    added_at: str


class ChannelResponse(BaseModel):
    id: int
    name: str
    webhook_url: str
    user_count: int
    created_at: Optional[str]


class StatusResponse(BaseModel):
    running: bool
    interval: int
    users_count: int
    channels_count: int
    credits_remaining: int  # This would need to be fetched from API


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    logger.info("API starting up...")
    yield
    # Shutdown
    if scheduler and scheduler.running:
        scheduler.stop()
        logger.info("Scheduler stopped")


app = FastAPI(title="Twitter Monitor Bot API", lifespan=lifespan)

# Serve static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Twitter Monitor Bot</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            h1 { color: #1da1f2; }
        </style>
    </head>
    <body>
        <h1>🐦 Twitter Monitor Bot</h1>
        <p>Loading...</p>
    </body>
    </html>
    """)


# Channel endpoints
@app.get("/api/channels", response_model=List[ChannelResponse])
async def get_channels():
    """Get all channels."""
    channels = db.list_channels()
    return [
        ChannelResponse(
            id=ch["id"],
            name=ch["name"],
            webhook_url=ch["webhook_url"],
            user_count=ch["user_count"],
            created_at=ch["created_at"]
        )
        for ch in channels
    ]


@app.post("/api/channels")
async def create_channel(channel: ChannelCreate):
    """Create a new channel."""
    try:
        channel_id = db.create_channel(channel.name, channel.webhook_url)
        return {"success": True, "id": channel_id, "message": f"Channel '{channel.name}' created"}
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail=f"Channel '{channel.name}' already exists")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/channels/{channel_name}")
async def delete_channel(channel_name: str):
    """Delete a channel."""
    try:
        deleted = db.delete_channel(channel_name)
        if deleted:
            return {"success": True, "message": f"Channel '{channel_name}' deleted"}
        raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# User endpoints
@app.get("/api/users", response_model=List[UserResponse])
async def get_users(channel: Optional[str] = None):
    """Get all users, optionally filtered by channel."""
    users = db.list_users(channel)
    return [
        UserResponse(
            id=u["id"],
            username=u["username"],
            channel_name=u["channel_name"],
            last_tweet_id=u["last_tweet_id"],
            is_active=u["is_active"],
            added_at=u["added_at"]
        )
        for u in users
    ]


@app.post("/api/users")
async def create_user(user: UserCreate, background_tasks: BackgroundTasks):
    """Add a new user to monitor."""
    # Normalize username
    username = user.username.strip().lower()
    if username.startswith("@"):
        username = username[1:]
    
    # Get channel
    channel = db.get_channel_by_name(user.channel_name)
    if not channel:
        raise HTTPException(status_code=404, detail=f"Channel '{user.channel_name}' not found")
    
    try:
        # Fetch initial tweet
        async with TwitterClient() as client:
            tweets = await client.get_last_tweets(username)
            last_tweet_id = None
            if tweets:
                last_tweet_id = max(tweets, key=lambda t: int(t.id)).id
        
        # Add to database
        user_id = db.add_user(username, channel.id, last_tweet_id)
        
        return {
            "success": True,
            "id": user_id,
            "username": username,
            "last_tweet_id": last_tweet_id,
            "message": f"User @{username} added to '{user.channel_name}'"
        }
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail=f"User @{username} already exists")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/users/{username}")
async def delete_user(username: str):
    """Remove a user from monitoring."""
    username = username.strip().lower()
    if username.startswith("@"):
        username = username[1:]
    
    try:
        deleted = db.remove_user(username)
        if deleted:
            return {"success": True, "message": f"User @{username} removed"}
        raise HTTPException(status_code=404, detail=f"User @{username} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Monitor control endpoints
@app.get("/api/status")
async def get_status():
    """Get current monitor status."""
    users = db.list_users()
    channels = db.list_channels()
    
    return StatusResponse(
        running=scheduler is not None and scheduler.running,
        interval=settings.CHECK_INTERVAL_SECONDS,
        users_count=len(users),
        channels_count=len(channels),
        credits_remaining=1020000  # Placeholder - would need to fetch from API
    )


@app.post("/api/monitor/start")
async def start_monitor(background_tasks: BackgroundTasks):
    """Start the monitoring loop."""
    global scheduler
    
    if scheduler and scheduler.running:
        return {"success": False, "message": "Monitor already running"}
    
    scheduler = Scheduler(interval=settings.CHECK_INTERVAL_SECONDS)
    
    # Run in background
    async def run_scheduler():
        await scheduler.run()
    
    background_tasks.add_task(run_scheduler)
    
    return {"success": True, "message": "Monitor started", "interval": settings.CHECK_INTERVAL_SECONDS}


@app.post("/api/monitor/stop")
async def stop_monitor():
    """Stop the monitoring loop."""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.stop()
        return {"success": True, "message": "Monitor stopped"}
    
    return {"success": False, "message": "Monitor not running"}


@app.post("/api/monitor/run-once")
async def run_once_check(background_tasks: BackgroundTasks):
    """Run a single monitoring cycle."""
    async def run_single():
        from scheduler import run_once
        await run_once()
    
    background_tasks.add_task(run_single)
    return {"success": True, "message": "Single check started"}


# Test endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/test/config")
async def test_config():
    """Check notification configuration."""
    from config import settings
    return {
        "telegram": {
            "enabled": settings.USE_TELEGRAM,
            "bot_token_set": bool(settings.TELEGRAM_BOT_TOKEN),
            "chat_id_set": bool(settings.TELEGRAM_CHAT_ID),
        },
        "twilio": {
            "account_sid_set": bool(settings.TWILIO_ACCOUNT_SID),
            "phone_number": settings.TWILIO_PHONE_NUMBER,
            "your_phone": settings.YOUR_PHONE_NUMBER,
        },
        "urgent_notifications_enabled": settings.URGENT_NOTIFICATIONS_ENABLED,
        "urgent_min_score": settings.URGENT_MIN_SCORE,
    }


@app.post("/api/test/telegram")
async def test_telegram():
    """Send a test Telegram message."""
    from config import settings
    
    if not settings.USE_TELEGRAM:
        return {"success": False, "error": "Telegram disabled. Set USE_TELEGRAM=true"}
    
    if not settings.TELEGRAM_BOT_TOKEN:
        return {"success": False, "error": "TELEGRAM_BOT_TOKEN not set"}
    
    if not settings.TELEGRAM_CHAT_ID:
        return {"success": False, "error": "TELEGRAM_CHAT_ID not set"}
    
    try:
        import httpx
        
        message = """🧪 *Test Alert from Twitter Bot*

This is a test message from your Twitter Monitor Bot!

If you see this, Telegram notifications are working ✅

Reply options:
1️⃣ INTERESTING - Send to Discord
2️⃣ NOTHING - Skip
3️⃣ BUILD - Create project"""
        
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            })
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Test sent! Check your Telegram.",
                    "cost": "$0.00 (FREE!)"
                }
            else:
                return {
                    "success": False,
                    "error": f"Telegram API error: {response.text}"
                }
                
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/test/urgent-notification")
async def test_urgent_notification():
    """
    Send a test urgent notification.
    Uses Telegram if configured (FREE), otherwise WhatsApp ($$$).
    """
    from urgent_notifier import UrgentNotifier
    from models import Tweet
    
    # Create a fake urgent tweet
    test_tweet = Tweet(
        id="1234567890123456789",
        text="🚀 BREAKING: Major crypto announcement! This could be huge for the market. Full details in thread...",
        created_at=datetime.now(),
        author_id="987654321",
        metrics={"likes": 25000, "retweets": 8000, "replies": 2000}
    )
    
    test_rating = {
        "score": 10,
        "category": "alpha",
        "summary": "Major market-moving announcement detected by AI",
        "reason": "High engagement and keyword analysis suggest this is significant alpha."
    }
    
    try:
        async with UrgentNotifier() as notifier:
            # Check configuration
            config_status = {
                "enabled": notifier.enabled,
                "telegram_configured": bool(notifier.telegram_bot_token and settings.USE_TELEGRAM),
                "twilio_configured": bool(notifier.twilio_sid and notifier.your_phone),
                "pushover_configured": bool(notifier.pushover_token),
            }
            
            if not notifier.is_configured():
                return {
                    "success": False,
                    "error": "No notification channels configured",
                    "config": config_status,
                    "message": "Set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID (FREE) or TWILIO_* ($$$)"
                }
            
            result = await notifier.send_urgent_notification(
                username="test_user",
                tweet=test_tweet,
                rating=test_rating
            )
            
            # Determine cost
            cost = "$0.00 (Telegram - FREE!)" if result.get("telegram", {}).get("sent") else "$0.04 (WhatsApp)"
            
            return {
                "success": result["sent"],
                "message": "Test sent! Check your phone." if result["sent"] else "Failed to send",
                "cost": cost,
                "config": config_status,
                "details": result
            }
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@app.post("/api/test/whatsapp")
async def test_whatsapp():
    """DEPRECATED: Use /api/test/urgent-notification instead."""
    return {
        "deprecated": True,
        "message": "Use /api/test/urgent-notification instead",
        "note": "Telegram is now the primary notification method (FREE!)"
    }


@app.post("/api/webhook/telegram")
async def telegram_webhook(request: dict):
    """
    Receive Telegram messages and callback queries.
    
    Handles:
    - Reply buttons: INTERESTING/NOTHING/BUILD
    - Direct text replies: 1/2/3 or I/N/B
    """
    from telegram_bot import telegram_bot
    
    try:
        # Handle callback queries (button clicks)
        if "callback_query" in request:
            callback = request["callback_query"]
            data = callback.get("data", "")
            chat_id = callback["message"]["chat"]["id"]
            message_id = callback["message"]["message_id"]
            
            logger.info(f"Telegram callback: {data}")
            
            # Parse action and tweet_id
            parts = data.split(":", 1)
            action = parts[0]
            tweet_id = parts[1] if len(parts) > 1 else None
            
            # Process action
            result = await telegram_bot.process_reply(action, tweet_id)
            
            # Answer callback
            await telegram_bot.answer_callback(callback["id"], result.get("message", "Done!"))
            
            # Update message to show action taken
            await telegram_bot.update_message(chat_id, message_id, action, result)
            
            return {"ok": True}
        
        # Handle direct messages (text replies)
        if "message" in request:
            message = request["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "").strip().upper()
            
            logger.info(f"Telegram message from {chat_id}: {text}")
            
            # Map replies to actions
            action_map = {
                "1": "INTERESTING", "I": "INTERESTING", "INTERESTING": "INTERESTING",
                "2": "NOTHING", "N": "NOTHING", "NOTHING": "NOTHING",
                "3": "BUILD", "B": "BUILD", "BUILD": "BUILD",
            }
            
            action = action_map.get(text)
            if action:
                result = await telegram_bot.process_reply(action)
                await telegram_bot.send_message(chat_id, result.get("message", f"Action: {action}"))
            else:
                await telegram_bot.send_message(
                    chat_id, 
                    "Reply with:\n1️⃣/I = INTERESTING\n2️⃣/N = NOTHING\n3️⃣/B = BUILD"
                )
            
            return {"ok": True}
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"ok": False, "error": str(e)}


@app.post("/api/webhook/twilio/whatsapp")
async def twilio_whatsapp_webhook(
    From: str = "",
    Body: str = "",
    MessageSid: str = ""
):
    """
    Receive WhatsApp replies from Twilio (fallback).
    
    User replies to urgent tweets with:
    - INTERESTING → Send to Discord
    - NOTHING → Skip/filter
    - BUILD → Create project
    """
    from whatsapp_handler import whatsapp_handler
    
    logger.info(f"WhatsApp reply from {From}: {Body}")
    
    # Process the reply
    response_message = await whatsapp_handler.process_reply(From, Body)
    
    # Return TwiML response (XML)
    from fastapi.responses import PlainTextResponse
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_message}</Message>
</Response>"""
    
    return PlainTextResponse(content=twiml, media_type="application/xml")


@app.get("/api/pending")
async def get_pending_tweets():
    """Get list of pending tweets awaiting user action."""
    from whatsapp_handler import whatsapp_handler
    
    return {
        "pending_count": whatsapp_handler.get_pending_count(),
        "pending": [
            {
                "phone": phone,
                "username": data["username"],
                "score": data["rating"].get("score", 0),
                "sent_at": data["sent_at"].isoformat(),
                "status": data["status"]
            }
            for phone, data in whatsapp_handler.pending_tweets.items()
        ]
    }


@app.get("/api/rate-limit")
async def get_rate_limit_status():
    """Get notification rate limiter status."""
    from rate_limiter import rate_limiter
    status = rate_limiter.get_status()
    queue = await rate_limiter.get_queue_status()
    return {"rate_limit": status, "queue": queue}


@app.post("/api/test/build")
async def test_build_agent():
    """
    Test the BUILD agent with a sample tweet.
    
    Runs full 6-stage pipeline:
    1. Kimi K2 - Analyze
    2. Kimi K2 - Plan  
    3. Kimi K2 - Design
    4. Qwen Coder - Implement (code + tests)
    5. Kimi K2 - Review
    6. Qwen Coder - Deploy config
    """
    from build_agent_enhanced import enhanced_build_agent
    
    # Test tweet - CLI tool example
    test_tweet = "Build a CLI tool that backs up all my GitHub repositories to local disk with progress bars and incremental updates"
    test_username = "test_user"
    
    logger.info("🧪 Testing BUILD agent with sample tweet...")
    logger.info(f"Tweet: {test_tweet}")
    
    try:
        # Run full build pipeline
        result = await enhanced_build_agent.build_project(test_tweet, test_username)
        
        if result["success"]:
            return {
                "success": True,
                "message": "✅ Build test completed successfully!",
                "project_name": result["project_name"],
                "project_path": result["project_path"],
                "tech_stack": result["tech_stack"],
                "stats": result["stats"],
                "build_log": result["build_log"],
                "next_steps": result["next_steps"][:3]  # First 3 steps
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "message": "❌ Build test failed"
            }
            
    except Exception as e:
        logger.error(f"Build test failed: {e}")
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.get("/api/models")
async def get_available_models():
    """Get available AI models and their pricing."""
    from ai_router import ai_router
    return {
        "models": ai_router.list_models(),
        "defaults": {
            "analysis": "kimi-k2 (excellent reasoning)",
            "code": "qwen-coder (40x cheaper, excellent code)"
        }
    }


@app.post("/api/test/complete")
async def test_complete():
    """
    Complete system test - verifies all components.
    Sends WhatsApp confirmation if everything works.
    """
    import subprocess
    import sys
    
    try:
        # Run the test script
        result = subprocess.run(
            [sys.executable, "test_complete.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr if result.stderr else None
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
