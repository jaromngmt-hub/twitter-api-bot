tweet_text = """Shipping a side project? Ship the landing page first.

A landing page is a commitment device, an invitation for feedback, and a forcing function all in one."""

username = "GuiBibeau"

print("="*70)
print(f"📝 Tweet by @{username}")
print(f"📄 Content:\n{tweet_text}")
print("="*70)

print("\n🔍 CORRECT Analysis (with fixed prompt):")
print("-"*70)

# CORRECT analysis
print("❌ This is NOT a product idea!")
print("✅ This is a METHAPHOR about product development")
print("   'Landing page' = metafora, nie produkt")
print("   Chodzi o: psychologię, metodologię, product management")
print()
print("🤦‍♂️ BŁĄD wcześniejszej analizy:")
print("   Landing page builder ❌")
print()
print("✅ POPRAWNA analiza:")
print("   To jest insight o tym JAK budować produkty")
print("   'Commitment device' = koncept psychologiczny")
print("   'Forcing function' = technika produktywności")
print()

analysis = {
    "should_send": True,
    "reason": "Valuable insight about product development psychology - not a product to build",
    "quality_score": 7,
    "category": "business",
    "is_original_content": True,
    "market_potential": "none",  # BO TO NIE PRODUKT
    "pioneer_opportunity": False,  # BO TO METAfora
    "build_alternative": None  # NIE MA CO BUDOWAĆ - to metoda, nie produkt
}

print(f"📊 Quality score: {analysis['quality_score']}/10")
print(f"💰 Market potential: {analysis['market_potential']} ← NIE JEST TO PRODUKT")
print(f"🔥 Pioneer opportunity: {analysis['pioneer_opportunity']}")
print(f"💡 Build alternative: {analysis['build_alternative']}")
print()

print("-"*70)
print("🎯 ROUTING: Discord (7/10 - good insight, but NOT a build opportunity)")
print("   Nie ma sensu budować 'landing page builder' - to nie o to chodzi!")
print("="*70)
