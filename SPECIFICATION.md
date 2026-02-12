# Twitter Monitor Bot - Complete Specification

## Overview
Build a production-ready multi-channel Twitter monitoring bot that tracks tweets from specified users and sends them to Discord channels. Features a web UI for easy management, REST API, and 24/7 cloud deployment capability.

## Core Features
1. **Multi-Channel Support**: Route tweets to different Discord channels based on groups
2. **Web UI**: Modern React-like interface for managing users and channels
3. **REST API**: Full CRUD operations for users, channels, and monitor control
4. **Smart Deduplication**: Never send the same tweet twice using Twitter snowflake IDs
5. **Background Monitoring**: Async scheduler that checks for new tweets every X minutes
6. **Discord Integration**: Rich embeds with tweet content, metrics, and media
7. **Cloud Ready**: Docker containerized with deployment configs for Render/Railway

## Architecture Stack

**Backend:**
- Python 3.11
- FastAPI (async web framework)
- SQLite (database)
- APScheduler (background jobs)
- httpx (async HTTP client)
- Loguru (logging)
- Pydantic (data validation)

**Frontend:**
- Vanilla HTML/CSS/JS (no framework needed)
- Modern CSS Grid/Flexbox
- Fetch API for REST calls
- Responsive design

**External APIs:**
- TwitterAPI.io (tweet fetching)
- Discord Webhooks (notifications)

**Deployment:**
- Docker containerization
- Render.com (free tier)
- Railway.app (alternative)

## Database Schema (SQLite)

```sql
-- Channels table (Discord channels)
CREATE TABLE channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    webhook_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Monitored users table
CREATE TABLE monitored_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL, -- stored lowercase, no @
    channel_id INTEGER,
    last_tweet_id TEXT, -- Twitter snowflake ID
    is_active BOOLEAN DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE
);

-- Sent tweets table (deduplication)
CREATE TABLE sent_tweets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tweet_id TEXT NOT NULL,
    username TEXT NOT NULL,
    channel_id INTEGER,
    text TEXT,
    created_at TIMESTAMP,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel_id) REFERENCES channels(id)
);

-- Indexes
CREATE INDEX idx_users_channel ON monitored_users(channel_id);
CREATE INDEX idx_sent_tweets_lookup ON sent_tweets(tweet_id, channel_id);
```

## API Endpoints

### Status
```
GET /api/health
Response: {"status": "healthy", "timestamp": "2024-01-01T00:00:00"}

GET /api/status
Response: {
    "running": false,
    "interval": 3600,
    "users_count": 5,
    "channels_count": 2
}
```

### Channels
```
GET /api/channels
Response: [{"id": 1, "name": "crypto", "webhook_url": "...", "user_count": 3}]

POST /api/channels
Body: {"name": "crypto", "webhook_url": "https://discord.com/api/webhooks/..."}
Response: {"success": true, "id": 1, "message": "Channel created"}

DELETE /api/channels/{name}
Response: {"success": true, "message": "Channel deleted"}
```

### Users
```
GET /api/users?channel={optional}
Response: [{
    "id": 1,
    "username": "elonmusk",
    "channel_name": "crypto",
    "last_tweet_id": "123456789",
    "is_active": true,
    "added_at": "2024-01-01T00:00:00"
}]

POST /api/users
Body: {"username": "elonmusk", "channel_name": "crypto"}
Response: {"success": true, "id": 1, "username": "elonmusk", "message": "User added"}

DELETE /api/users/{username}
Response: {"success": true, "message": "User removed"}
```

### Monitor Control
```
POST /api/monitor/start
Response: {"success": true, "message": "Monitor started"}

POST /api/monitor/stop
Response: {"success": true, "message": "Monitor stopped"}

POST /api/monitor/run-once
Response: {"success": true, "message": "Single check started"}
```

## Frontend UI Components

### Layout
```
┌─────────────────────────────────────────────────────────┐
│ HEADER: Logo + Status Indicator (Running/Stopped)       │
├─────────────────────────────────────────────────────────┤
│ STATS CARDS: Users | Channels | Credits | Interval      │
├─────────────────────────────────────────────────────────┤
│ CONTROL PANEL: [Start] [Stop] [Run Once] [Refresh]      │
├─────────────────────────────────────────────────────────┤
│ ADD USER: [Input: @username] [Channel Select] [Add]     │
├─────────────────────────────────────────────────────────┤
│ ADD CHANNEL: [Name] [Webhook URL] [Add]                 │
├─────────────────────────────────────────────────────────┤
│ USERS TABLE: Username | Channel | Status | Actions      │
├─────────────────────────────────────────────────────────┤
│ CHANNELS TABLE: Name | Webhook | Users | Actions        │
├─────────────────────────────────────────────────────────┤
│ LOGS: Real-time scrollable logs                         │
└─────────────────────────────────────────────────────────┘
```

### Design Specs
- **Primary Color**: Twitter blue (#1da1f2)
- **Success**: Green (#28a745)
- **Danger**: Red (#dc3545)
- **Background**: Light gray (#f5f8fa)
- **Cards**: White with shadow
- **Font**: System fonts (-apple-system, BlinkMacSystemFont, Segoe UI)
- **Responsive**: Mobile-friendly grid

## Monitoring Logic (Critical)

### Algorithm
```python
1. Load all active users with their channels
2. For each user (async parallel):
   a. Call TwitterAPI.io /twitter/user/last_tweets?userName={username}
   b. If last_tweet_id is NULL:
      - Take most recent tweet ID
      - Update DB (DO NOT SEND - prevent spam)
   c. If last_tweet_id exists:
      - Filter tweets where tweet.id > last_tweet_id
      - Sort by created_at ascending (oldest first)
      - For each new tweet:
        * Check sent_tweets table (dedup)
        * Send to Discord webhook
        * Insert into sent_tweets
        * Sleep 1s between sends (rate limit)
      - Update last_tweet_id to newest
3. Wait interval seconds, repeat
```

### TwitterAPI.io Integration
```
Endpoint: GET https://api.twitterapi.io/twitter/user/last_tweets?userName={username}
Headers: {"x-api-key": "YOUR_API_KEY"}

Response Format:
{
  "status": "success",
  "data": {
    "tweets": [
      {
        "id": "123456789",
        "text": "Tweet content",
        "created_at": "2024-01-01T00:00:00.000Z",
        "public_metrics": {
          "like_count": 100,
          "retweet_count": 50,
          "reply_count": 20
        },
        "entities": {
          "media": [{"type": "photo", "url": "..."}]
        }
      }
    ]
  }
}

Rate Limit: 1 request per 5 seconds (free tier)
Error Handling:
- 429: Exponential backoff (2s, 4s, 8s)
- 404: Mark user as inactive
- 401: Exit with error
```

### Discord Webhook Format
```json
{
  "username": "@elonmusk",
  "avatar_url": "https://unavatar.io/twitter/elonmusk",
  "embeds": [{
    "description": "Tweet text here...",
    "color": 1942002,
    "timestamp": "2024-01-01T00:00:00.000Z",
    "footer": {
      "text": "@elonmusk | ❤️ 100 | 🔁 50 | 💬 20"
    },
    "image": {"url": "media_url_if_exists"}
  }]
}
```

## File Structure

```
twitter-monitor/
├── api.py                 # FastAPI backend
├── main.py               # CLI entry point
├── scheduler.py          # Background monitoring
├── twitter_client.py     # TwitterAPI.io integration
├── discord_client.py     # Discord webhook sender
├── database.py           # SQLite operations
├── models.py             # Pydantic models
├── config.py             # Settings management
├── requirements.txt      # Python dependencies
├── Dockerfile            # Main Docker image
├── Dockerfile.render     # Optimized for Render
├── start.sh              # Startup script
├── render.yaml           # Render deployment config
├── docker-compose.yml    # Local development
├── .env.example          # Environment template
├── .dockerignore
├── static/               # Frontend files
│   ├── index.html       # Main UI
│   ├── style.css        # Styles
│   └── app.js           # Frontend logic
└── data/                # Database storage
```

## Key Code Files

### config.py
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    TWITTERAPI_KEY: str = os.getenv("TWITTERAPI_KEY", "")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./monitor.db")
    CHECK_INTERVAL_SECONDS: int = int(os.getenv("CHECK_INTERVAL_SECONDS", "3600"))
    MAX_TWEETS_PER_CHECK: int = int(os.getenv("MAX_TWEETS_PER_CHECK", "20"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
```

### models.py
```python
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Tweet(BaseModel):
    id: str
    text: str
    created_at: datetime
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    media_urls: List[str] = []

class Channel(BaseModel):
    id: int
    name: str
    webhook_url: str

class MonitoredUser(BaseModel):
    id: int
    username: str
    channel_id: int
    last_tweet_id: Optional[str] = None
    is_active: bool = True
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data /app/logs /app/static

EXPOSE 8000

CMD ["/app/start.sh"]
```

### start.sh
```bash
#!/bin/sh
if [ -n "$PORT" ]; then
    uvicorn api:app --host 0.0.0.0 --port $PORT
else
    python main.py run
fi
```

### render.yaml
```yaml
services:
  - type: web
    name: twitter-api-bot
    runtime: docker
    plan: free
    dockerfilePath: Dockerfile
    envVars:
      - key: DATABASE_PATH
        value: /app/data/monitor.db
      - key: CHECK_INTERVAL_SECONDS
        value: "3600"
      - key: PORT
        value: "8000"
    disk:
      name: data
      mountPath: /app/data
      sizeGB: 1
```

## Deployment Instructions

### Local Development
```bash
pip install -r requirements.txt
python main.py init
python main.py channel create alerts WEBHOOK_URL
python main.py user add elonmusk alerts
python main.py run
```

### Docker Local
```bash
docker-compose up -d
open http://localhost:8000
```

### Render.com Deployment
1. Push code to GitHub
2. Connect repo on Render
3. Select "Web Service"
4. Runtime: Docker
5. Add environment variable: TWITTERAPI_KEY
6. Deploy!

## Cost Analysis

**Free Tier Options:**
- Render.com: Free (sleeps after 15min, use cron-job.org to ping)
- Railway: $5/month (always on)
- Oracle Cloud: Always free tier (2 VMs, never expires)

**API Costs:**
- TwitterAPI.io: $10 for 1,000,000 credits
- 200 users @ 1 hour interval = ~144,000 calls/month
- $10 lasts ~7 months

## Security Considerations

1. **API Keys**: Store in environment variables, never commit
2. **Database**: SQLite with foreign key constraints
3. **Rate Limiting**: Respect TwitterAPI 1 req/5s limit
4. **Input Validation**: Normalize usernames (lowercase, strip @)
5. **Discord**: Validate webhook URL format

## Testing Checklist

- [ ] Create channel with webhook
- [ ] Add user (fetches initial tweet)
- [ ] Start monitor
- [ ] Verify Discord receives new tweets
- [ ] Check deduplication (no duplicates)
- [ ] Delete user
- [ ] Delete channel
- [ ] API endpoints respond correctly
- [ ] Web UI loads and functions

## Future Enhancements

1. Per-user check intervals (VIP users check more often)
2. Keyword filtering (only tweets containing X)
3. Multiple Discord channels per user
4. Tweet reply/quote threading
5. Analytics dashboard
6. Mobile app
7. Slack/Teams integration

---

This specification is complete and ready for implementation by any AI coding assistant or developer.
