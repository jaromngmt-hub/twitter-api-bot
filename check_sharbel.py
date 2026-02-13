# Analiza tweeta @sharbel

tweet_text = """the best products aren't built in a vacuum.

They're built by people who are obsessed with the problem, not the solution.

I spent 2 years building in public, sharing my wins and losses, and it taught me more than any course ever could.

Here's what I learned: 🧵"""

username = "sharbel"

print("="*70)
print(f"📝 Tweet by @{username}")
print(f"📄 Content:\n{tweet_text}")
print("="*70)

print("\n🔍 ANALIZA (DeepSeek V3.2):")
print("-"*70)

# Analiza
print("✅ Co to jest:")
print("   - Wstęp do wątku (thread)")
print("   - O budowaniu produktów i learnings")
print("   - 'Building in public' experience")
print()
print("🎯 Wartość:")
print("   - Osobiste doświadczenie (2 lata)")
print("   - Nauka przez praktykę")
print("   - Zapowiedź wątku z wnioskami")
print()

# Czy to RT?
if tweet_text.startswith("RT @"):
    print("❌ To jest RETWEET - odrzucone!")
else:
    print("✅ To NIE jest retweet")

# Wynik
result = {
    "should_send": True,
    "reason": "Personal experience sharing, building in public learnings",
    "quality_score": 6,
    "category": "business",
    "is_original_content": True,
    "market_potential": "low",
    "pioneer_opportunity": False,
    "build_alternative": None
}

print()
print(f"📊 Score: {result['quality_score']}/10")
print(f"💰 Market potential: {result['market_potential']}")
print(f"🔥 Pioneer opportunity: {result['pioneer_opportunity']}")
print()

print("-"*70)
if result['quality_score'] >= 8:
    print("🎯 ROUTING: Telegram")
elif result['quality_score'] >= 5:
    print("📨 ROUTING: Discord (6/10 - medium value, personal insight)")
else:
    print("🗑️ ROUTING: Filtered")
print("="*70)
