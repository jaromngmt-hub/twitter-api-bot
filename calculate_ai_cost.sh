#!/bin/bash
echo "=== DZIENNE ZUŻYCIE TOKENÓW AI ==="
echo ""
echo "Założenia:"
echo "  - 15 użytkowników"
echo "  - 5 tweetów na użytkownika (MAX_TWEETS_PER_CHECK=5)"
echo "  - Sprawdzanie co 1h (CHECK_INTERVAL=3600s)"
echo "  - 24 cykle dziennie"
echo ""

USERS=15
TWEETS_PER_USER=5
CYCLES_PER_DAY=24

TOTAL_TWEETS=$((USERS * TWEETS_PER_USER * CYCLES_PER_DAY))
echo "Tweetów dziennie: $TOTAL_TWEETS"
echo ""

echo "Tokeny na analizę (gpt-3.5-turbo było):"
echo "  Input: ~500 tokenów"
echo "  Output: ~200 tokenów"
echo "  Razem: ~700 tokenów/tweet"
echo ""

DAILY_TOKENS=$((TOTAL_TWEETS * 700))
echo "DZIENNE ZUŻYCIE: $DAILY_TOKENS tokenów"
echo ""

echo "=== KOSZTY ==="
echo "GPT-3.5-turbo: \$0.50/1M input, \$1.50/1M output"
INPUT_COST=$(echo "scale=4; $DAILY_TOKENS * 0.5 / 1000000" | bc)
OUTPUT_COST=$(echo "scale=4; $DAILY_TOKENS * 1.5 / 1000000" | bc)
echo "  Input: \$$INPUT_COST"
echo "  Output: \$$OUTPUT_COST"
echo ""

echo "DeepSeek V3.2 (TERAZ): \$0.25/1M input, \$0.38/1M output"
INPUT_COST_DS=$(echo "scale=4; $DAILY_TOKENS * 0.25 / 1000000" | bc)
OUTPUT_COST_DS=$(echo "scale=4; $DAILY_TOKENS * 0.38 / 1000000" | bc)
echo "  Input: \$$INPUT_COST_DS"
echo "  Output: \$$OUTPUT_COST_DS"
