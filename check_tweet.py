# Analiza tweeta @infinterenders
# "if you want to build an ai agent that can actually make money, 
# you need to give it a skill that people pay for."

tweet_text = """if you want to build an ai agent that can actually make money, you need to give it a skill that people pay for.

here's the skill i gave mine:

→ built a solana skill for my solana agent
→ it can trade, stake, and manage portfolios
→ people pay for automated trading strategies"""

username = "infinterenders"

print("="*70)
print(f"📝 Tweet by @{username}")
print(f"📄 Content:\n{tweet_text}")
print("="*70)

print("\n🔍 ANALIZA (DeepSeek V3.2):")
print("-"*70)

# Analiza
print("✅ Co to jest:")
print("   - Case study / proof of concept")
print("   - Konkretny przykład monetyzacji AI agenta")
print("   - Solana blockchain + trading")
print()
print("🎯 Wartość:")
print("   - Pokazuje JAK zarabiać na AI agentach")
print("   - Konkretna nisza (Solana trading)")
print("   - Actionable insight")
print()

# Wynik
result = {
    "should_send": True,
    "reason": "Case study showing monetization of AI agent with Solana trading skill",
    "quality_score": 8,
    "category": "crypto",
    "is_original_content": True,
    "market_potential": "high",
    "pioneer_opportunity": True,
    "build_alternative": "Multi-chain AI trading agent with portfolio management"
}

print(f"📊 Score: {result['quality_score']}/10")
print(f"💰 Market potential: {result['market_potential']}")
print(f"🔥 Pioneer opportunity: {result['pioneer_opportunity']}")
print(f"💡 Build idea: {result['build_alternative']}")
print()

print("-"*70)
if result['quality_score'] >= 8 and result['pioneer_opportunity']:
    print("🎯 ROUTING: Telegram (URGENT + BUILD buttons)")
    print("   Dlaczego: Wysoki score + można zbudować alternatywę!")
else:
    print("📨 ROUTING: Discord")
print("="*70)
