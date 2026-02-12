#!/usr/bin/env python3
"""Test WhatsApp urgent notification."""

import asyncio
import sys
from datetime import datetime

from loguru import logger

# Setup logging
logger.remove()
logger.add(sys.stdout, level="INFO")

from urgent_notifier import UrgentNotifier
from models import Tweet


async def test_whatsapp():
    """Send a test WhatsApp urgent notification."""
    
    # Create a fake high-value tweet
    test_tweet = Tweet(
        id="1234567890",
        text="🚀 BREAKING: Ethereum just announced massive scaling upgrade! This changes everything for L2s. Full details in thread...",
        created_at=datetime.now(),
        author_id="987654321",
        metrics={"likes": 15000, "retweets": 5000, "replies": 1200}
    )
    
    # Create a fake high rating (score 10)
    test_rating = {
        "score": 10,
        "category": "alpha",
        "summary": "Ethereum scaling upgrade announcement - major alpha for L2 ecosystem",
        "reason": "Market-moving news that could significantly impact ETH and L2 token prices. High engagement suggests validation."
    }
    
    print("🧪 Testing WhatsApp urgent notification...")
    print(f"   Score: {test_rating['score']}/10")
    print(f"   From: @test_user")
    print(f"   Category: {test_rating['category']}")
    print()
    
    async with UrgentNotifier() as notifier:
        # Check if configured
        if not notifier.is_configured():
            print("❌ ERROR: No notification channels configured!")
            print("   Make sure these env vars are set:")
            print("   - TWILIO_ACCOUNT_SID")
            print("   - TWILIO_AUTH_TOKEN")
            print("   - TWILIO_PHONE_NUMBER")
            print("   - YOUR_PHONE_NUMBER")
            print("   - URGENT_NOTIFICATIONS_ENABLED=true")
            return False
        
        # Check if enabled
        if not notifier.enabled:
            print("❌ ERROR: URGENT_NOTIFICATIONS_ENABLED is not set to 'true'")
            return False
        
        print("✅ Configuration looks good!")
        print(f"   Twilio SID: {notifier.twilio_sid[:10]}...")
        print(f"   Your phone: {notifier.your_phone}")
        print()
        
        # Send the notification
        print("📱 Sending WhatsApp test message...")
        result = await notifier.send_urgent_notification(
            username="test_user",
            tweet=test_tweet,
            rating=test_rating
        )
        
        print()
        print("📊 RESULT:")
        print(f"   Sent: {result['sent']}")
        print(f"   Score: {result['score']}")
        print(f"   Username: {result['username']}")
        
        if result['sent']:
            print()
            print("✅ SUCCESS! Check your WhatsApp now!")
            print("   You should receive a message from Twilio's WhatsApp number.")
            
            # Show which channels worked
            for channel, status in result.get('channels', {}).items():
                icon = "✅" if status.get('sent') else "❌"
                print(f"   {icon} {channel}: {status}")
        else:
            print()
            print("❌ FAILED!")
            for channel, status in result.get('channels', {}).items():
                if not status.get('sent'):
                    print(f"   ❌ {channel}: {status.get('error', 'Unknown error')}")
        
        return result['sent']


if __name__ == "__main__":
    success = asyncio.run(test_whatsapp())
    sys.exit(0 if success else 1)
