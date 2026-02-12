#!/bin/bash
# Auto-deploy script - Run this after making changes

echo "🚀 Starting auto-deployment..."

# Step 1: Commit changes
echo "📦 Committing changes..."
git add .
git commit -m "Auto-update: $(date '+%Y-%m-%d %H:%M:%S')"

# Step 2: Push to GitHub
echo "☁️ Pushing to GitHub..."
git push origin main

# Step 3: Trigger Render deploy
echo "🔄 Triggering Render deployment..."
curl -s "https://api.render.com/deploy/srv-d66dmm9r0fns73dk3m1g?key=dyqIAY_0r18"

echo ""
echo "✅ DONE! Changes deployed to:"
echo "   https://twitter-api-bot.onrender.com"
echo ""
echo "⏳ Wait 2-3 minutes for build to complete"
