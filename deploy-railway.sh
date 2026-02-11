#!/bin/bash

# Deploy Twitter Monitor Bot to Railway

echo "🚀 Deploying to Railway..."
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found!"
    echo "Install with: brew install railway"
    echo "Or: npm install -g @railway/cli"
    exit 1
fi

# Login to Railway
echo "🔑 Logging in to Railway..."
railway login

# Initialize project (if not already)
if [ ! -f .railway/config.json ]; then
    echo "📦 Initializing Railway project..."
    railway init
fi

# Set environment variables
echo "⚙️ Setting environment variables..."
railway variables set DATABASE_PATH=/app/data/monitor.db
railway variables set CHECK_INTERVAL_SECONDS=3600
railway variables set MAX_TWEETS_PER_CHECK=20
railway variables set LOG_LEVEL=INFO

# Prompt for API key
echo ""
echo "🔑 Enter your TwitterAPI.io key:"
read -s TWITTERAPI_KEY
railway variables set TWITTERAPI_KEY="$TWITTERAPI_KEY"

echo ""
echo "🚀 Deploying..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Your bot is live at:"
railway domain

echo ""
echo "📊 Monitor logs with: railway logs"
