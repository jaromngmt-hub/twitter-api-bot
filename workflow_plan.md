# WORKFLOW - Analiza i zapisywanie pomysłów

## OBECNY FLOW:
```
Tweet (score 8+) 
    ↓
Telegram z 3 przyciskami:
    ├─ [INTERESTING] → Zapisz na Discord "interesting" channel
    ├─ [BUILD]       → Rozpocznij build proces
    └─ [NOTHING]     → Odrzuć
```

## CO SIE DZIEJE:

### 1. INTERESTING (zapisz do analizy)
```
User klika INTERESTING
    ↓
Tweet zapisany na Discord #interesting
    ├─ Treść tweeta
    ├─ Link do oryginału
    ├─ Autor
    ├─ Dlaczego jest ciekawy (AI reason)
    └─ Timestamp
    ↓
Możesz później przejrzeć i zdecydować czy budować
```

### 2. BUILD (buduj teraz)
```
User klika BUILD
    ↓
Rozpoczyna się build proces
    ↓
Bot pyta: DEFAULT czy CUSTOM requirements
    ↓
Build trwa ~10-15 min
    ↓
Gotowy projekt na GitHubie
```

### 3. NOTHING (odrzuć)
```
User klika NOTHING
    ↓
Tweet oznaczony jako "przeczytany"
    ↓
Nie zapisujemy nigdzie
```

## PRZYKŁADY:

### Tweet 1: "Shipfast w Pythonie"
```
Score: 8/10
Telegram: "Ktoś chce zbudować Shipfast w Pythonie"

Opcje:
├─ [INTERESTING] → Zapisz na Discord #interesting 
│                  (pomysł na produkt, może warto zrobić)
├─ [BUILD]       → Zacznij budować od razu
└─ [NOTHING]     → Pomijamy

User wybiera: INTERESTING
Efekt: Zapisane na Discord, user może wrócić do tego za tydzień
```

### Tweet 2: "Solana skill dla AI agenta"
```
Score: 9/10
Telegram: "Case study: AI agent handlujący Solana"

User wybiera: BUILD
Efekt: Bot buduje "Multi-chain AI trading agent"
```

### Tweet 3: "Landing page jako commitment device"
```
Score: 7/10 (metafora, nie produkt)
Telegram: "Wątek o psychologii budowania produktów"

User wybiera: NOTHING
Efekt: Odrzucone, nie zapisujemy
```

## DISCORD #interesting CHANNEL:

Tak wyglądają zapisane pomysły:
```
📝 INTERESTING IDEA

Tweet by @tech_nurgaliyev
"Shipfast alternative in Python..."

💡 Dlaczego ciekawe:
   - Market validation (pyta o zainteresowanie)
   - Można zbudować alternatywę
   - Python popularny

🔗 Link: https://twitter.com/...
📅 Zapisano: 2024-02-13 15:30

[ZOBACZ NA DC] [BUDUJ TERAZ]
```

## CZY TO O TO CHODZI?

✅ Wszystkie fajne pomysły przychodzą na Telegram
✅ Możesz szybko oznaczyć jako INTERESTING (zapisz na później)
✅ Nie musisz budować od razu - analizujesz kiedy chcesz
✅ Discord #interesting = twoja "baza pomysłów"
✅ BUILD tylko gdy naprawdę chcesz budować

Czy tak ma działać?
