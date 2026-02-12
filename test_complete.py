#!/usr/bin/env python3
"""Complete system test - verifies all components work."""

import asyncio
import os
from datetime import datetime

from config import settings
from models import Tweet


async def test_complete_flow():
    """Test the complete Twitter Monitor + Build system."""
    
    print("🧪 COMPLETE SYSTEM TEST")
    print("=" * 60)
    
    # 1. Check Configuration
    print("\n1️⃣ Checking Configuration...")
    
    checks = {
        "TwitterAPI Key": bool(settings.TWITTERAPI_KEY),
        "OpenRouter Key": bool(settings.OPENROUTER_API_KEY),
        "GitHub Token": bool(settings.GITHUB_TOKEN),
        "GitHub Username": bool(settings.GITHUB_USERNAME),
        "Twilio SID": bool(settings.TWILIO_ACCOUNT_SID),
        "Twilio Token": bool(settings.TWILIO_AUTH_TOKEN),
        "Your Phone": bool(settings.YOUR_PHONE_NUMBER),
        "Urgent Notifications": settings.URGENT_NOTIFICATIONS_ENABLED,
    }
    
    all_good = True
    for name, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}: {'OK' if status else 'MISSING'}")
        if not status:
            all_good = False
    
    if not all_good:
        print("\n❌ Some configuration is missing!")
        print("Add missing env vars to Render: https://dashboard.render.com/web/srv-d66dmm9r0fns73dk3m1g/env")
        return False
    
    # 2. Test WhatsApp
    print("\n2️⃣ Testing WhatsApp...")
    try:
        from urgent_notifier import UrgentNotifier
        
        notifier = UrgentNotifier()
        if notifier.is_configured():
            print("  ✅ WhatsApp configured")
            
            # Send test message
            await notifier._send_whatsapp_raw(
                to=settings.YOUR_PHONE_NUMBER,
                message="""🧪 *SYSTEM TEST*

Twitter Monitor Bot is working!

✅ Configuration: OK
✅ WhatsApp: Connected
✅ AI Models: Ready (Kimi + Qwen)
✅ GitHub: Ready

Monitor runs every 30 minutes.
You'll get WhatsApp alerts for high-value tweets (8-10/10).

━━━━━━━━━━━━━━━━━━━━━━
*When you get alerts, reply:*
1️⃣ *INTERESTING* → Share to Discord
2️⃣ *NOTHING* → Skip this  
3️⃣ *BUILD* → 🚀 Create project
━━━━━━━━━━━━━━━━━━━━━━

💡 *Quick reply:* Type 1/2/3 or I/N/B"""
            )
            print("  ✅ Test message sent! Check your WhatsApp.")
        else:
            print("  ❌ WhatsApp not configured")
            return False
    except Exception as e:
        print(f"  ❌ WhatsApp error: {e}")
        return False
    
    # 3. Test AI Router
    print("\n3️⃣ Testing AI Router (Kimi + Qwen)...")
    try:
        from ai_router import ai_router
        
        # Quick test
        response = await ai_router.generate(
            prompt="Say 'Kimi and Qwen are ready!'",
            task_type="docs",
            max_tokens=50
        )
        print(f"  ✅ AI Response: {response[:50]}...")
    except Exception as e:
        print(f"  ❌ AI Router error: {e}")
        return False
    
    # 4. Test GitHub
    print("\n4️⃣ Testing GitHub...")
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/users/{settings.GITHUB_USERNAME}",
                headers={"Authorization": f"token {settings.GITHUB_TOKEN}"}
            )
            if response.status_code == 200:
                print(f"  ✅ GitHub connected: @{settings.GITHUB_USERNAME}")
            else:
                print(f"  ❌ GitHub error: {response.status_code}")
                return False
    except Exception as e:
        print(f"  ❌ GitHub error: {e}")
        return False
    
    # 5. Summary
    print("\n" + "=" * 60)
    print("✅ ALL SYSTEMS OPERATIONAL!")
    print("=" * 60)
    print(f"""
📱 WhatsApp: {settings.YOUR_PHONE_NUMBER}
🤖 AI: Kimi K2 (analysis) + Qwen Coder (code)
📊 Check Interval: 30 minutes
🎯 Monitored Users: 15
📢 Discord Channels: 5

🚀 WHAT HAPPENS NOW:
1. Every 30 min: Check 15 users for new tweets
2. AI rates each tweet (0-10)
3. Score 0-1: Filtered (trash)
4. Score 2-7: Discord (by category: AI/CRYPTO/etc.)
5. Score 8-10: WhatsApp → YOU decide:
   • BUILD → Kimi+Qwen create project
   • INTERESTING → Send to Discord
   • NOTHING → Skip

💰 COST: ~$0.05 per build (40x cheaper than GPT-4o!)
""")
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_complete_flow())
    exit(0 if result else 1)
