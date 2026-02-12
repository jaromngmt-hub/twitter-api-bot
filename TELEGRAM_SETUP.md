# 📱 Telegram Bot Setup Guide

Switch from expensive WhatsApp ($0.04/msg) to **FREE** Telegram messaging!

## 💰 Cost Comparison

| Service | Cost per message | Monthly (100 alerts) |
|---------|-----------------|---------------------|
| Twilio WhatsApp | $0.04 | **$4.00** |
| Twilio SMS | $0.0075 | **$0.75** |
| **Telegram** | **$0.00** | **FREE!** 🎉 |

## 🚀 Quick Setup (2 minutes)

### Step 1: Create Bot
1. Open Telegram and message **@BotFather**
2. Send: `/newbot`
3. Follow prompts:
   - Name: `Twitter Monitor Bot`
   - Username: `yourname_twitter_bot` (must end in _bot, unique)
4. **Copy the token** (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Chat ID
1. Message **@userinfobot**
2. It will reply with your ID (looks like `123456789`)
3. **Copy the ID**

### Step 3: Set Environment Variables

Add to your `.env` file or Render dashboard:

```bash
USE_TELEGRAM=true
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Step 4: Set Webhook (Optional but Recommended)

For reply buttons to work, set the webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-app.onrender.com/api/webhook/telegram"}'
```

Or visit this URL in your browser:
```
https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://your-app.onrender.com/api/webhook/telegram
```

## ✅ Testing

Once deployed, test with:

```bash
curl -X POST https://your-app.onrender.com/api/test/telegram
```

Or visit: `https://your-app.onrender.com/api/test/telegram`

## 🎯 How It Works

When a tweet scores 8-10/10:

1. **Bot sends message** with:
   - Tweet text (truncated)
   - Score & category
   - Why it's important
   - **3 buttons**: INTERESTING / NOTHING / BUILD

2. **You reply** by:
   - Clicking a button
   - Or typing: `1`/`2`/`3` or `I`/`N`/`B`

3. **Actions**:
   - **INTERESTING** → Sent to Discord #interesting channel
   - **NOTHING** → Tweet skipped/filtered
   - **BUILD** → Kimi K2 + Qwen Coder create a project!

## 🔧 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/test/telegram` | Send test message |
| `POST /api/test/urgent-notification` | Test full urgent flow |
| `POST /api/webhook/telegram` | Receive bot updates |
| `GET /api/test/config` | Check all notification settings |

## 🛟 Troubleshooting

**Bot not sending messages?**
- Check `USE_TELEGRAM=true` in env vars
- Verify token format: `123456789:ABC...`
- Verify chat ID is just numbers: `123456789`
- Check Render logs: `https://dashboard.render.com/web/YOUR_SERVICE/logs`

**Buttons not working?**
- Webhook not set - use Step 4 above
- Or poll manually (not recommended)

**Want to use both Telegram AND WhatsApp?**
- Set both configs
- Telegram is tried first (FREE)
- WhatsApp is fallback ($$$)

## 📊 Monitoring

Check pending tweets awaiting your action:
```bash
curl https://your-app.onrender.com/api/pending
```

## 🎉 Success!

You now have **FREE unlimited messaging** for your Twitter bot!

Next: [Set up Discord webhooks](DISCORD_SETUP.md) (if not done)
