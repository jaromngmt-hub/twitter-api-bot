#!/bin/bash
# Dodaj użytkowników przez API

URL="https://twitter-api-bot.onrender.com/api"

# Dodaj użytkowników
curl -X POST "$URL/users" -H "Content-Type: application/json" -d '{"username":"exm7777","channel_name":"AI"}' 2>/dev/null
curl -X POST "$URL/users" -H "Content-Type: application/json" -d '{"username":"godofprompt","channel_name":"PROMPT"}' 2>/dev/null
curl -X POST "$URL/users" -H "Content-Type: application/json" -d '{"username":"defi_explora","channel_name":"CRYPTO"}' 2>/dev/null

echo "Dodano!"
