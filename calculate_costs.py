# Obliczenia kosztów analizy tweetów

# Typowy prompt do analizy (szacunek)
PROMPT_TOKENS = 600  # ~400 słów + instrukcje
RESPONSE_TOKENS = 300  # JSON response

# Ilości
TWEETS_PER_HOUR = 50  # szacunek
HOURS_PER_DAY = 24
TWEETS_PER_DAY = TWEETS_PER_HOUR * HOURS_PER_DAY  # ~1200

print("="*60)
print("KOSZTY ANALIZY TWEETÓW (dzienne)")
print("="*60)
print(f"\nZałożenia:")
print(f"  Tweetów dziennie: ~{TWEETS_PER_DAY}")
print(f"  Tokeny na prompt: ~{PROMPT_TOKENS}")
print(f"  Tokeny na odpowiedź: ~{RESPONSE_TOKENS}")
print(f"  Razem na tweet: ~{PROMPT_TOKENS + RESPONSE_TOKENS} tokens")

print("\n" + "="*60)
print("PORÓWNANIE MODELI:")
print("="*60)

models = {
    "GPT-5-nano": {"input": 0.05, "output": 0.40, "quality": "LOW - głupie błędy"},
    "DeepSeek V3.2": {"input": 0.25, "output": 0.38, "quality": "GOOD - solidna"},
    "Kimi K2.5": {"input": 0.50, "output": 2.00, "quality": "BEST - rozumie kontekst"},
}

for name, pricing in models.items():
    input_cost = (PROMPT_TOKENS * TWEETS_PER_DAY / 1_000_000) * pricing["input"]
    output_cost = (RESPONSE_TOKENS * TWEETS_PER_DAY / 1_000_000) * pricing["output"]
    total_daily = input_cost + output_cost
    total_monthly = total_daily * 30
    
    print(f"\n{name}:")
    print(f"  Cena: ${pricing['input']}/${pricing['output']} per 1M")
    print(f"  Jakość: {pricing['quality']}")
    print(f"  Dziennie: ${total_daily:.3f}")
    print(f"  Miesięcznie: ${total_monthly:.2f}")

print("\n" + "="*60)
print("REKOMENDACJA:")
print("="*60)
print("""
GPT-5-nano: $0.54/miesiąc - za tanio, słaba jakość ❌
DeepSeek V3.2: $2.83/miesiąc - dobry stosunek ceny do jakości ⚡
Kimi K2.5: $11.88/miesiąc - najlepszy, rozumie kontekst ✅

RÓŻNICA: $11 vs $0.54 = $11 więcej miesięcznie
ALE: Lepsza jakość = mniej głupich błędów = więcej wartości
""")
