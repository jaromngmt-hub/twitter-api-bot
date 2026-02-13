# Porównanie Twitter API - dla skali

## Obecne: TwitterAPI.io
- Cena: $0.0015 / request
- Przy 900 req/dzień = $40.50/miesiąc
- Przy skali (10k req/dzień) = $450/miesiąc ❌

## Tańsze alternatywy:

### 1. **RapidAPI Twitter** 
- Cena: ~$0.0003 / request (5x taniej!)
- Free tier: 100 req/dzień
- Basic: $10/miesiąc = 10k req/dzień
- Link: rapidapi.com/twitter-api

### 2. **ScraperAPI + Twitter** (najtańsze!)
- Cena: $0.0001 / request (15x taniej!)
- $49/miesiąc = nieograniczone proxy
- Sam scrapujesz HTML Twittera
- Wymaga parsera

### 3. **Official Twitter API v2** (dla dużej skali)
- Basic: $100/miesiąc = 10k req/miesiąc
- Pro: $5000/miesiąc = 1M req/miesiąc
- Najbardziej niezawodne
- Rate limity są OK

### 4. **Nitter instances** (FREE ale niestabilne)
- Cena: $0
- Publiczne instancje często padają
- Własna instancja: $5/miesiąc VPS
- Ryzko blokady przez Twitter

## Rekomendacja dla skali:

| Skala | Opcja | Koszt/miesiąc |
|-------|-------|---------------|
| <1k req/dzień | TwitterAPI.io | $50 |
| 1-10k req/dzień | RapidAPI | $30-100 |
| >10k req/dzień | ScraperAPI + parser | $50-100 |
| Enterprise | Official Twitter API | $5000+ |

## Najlepsze dla nas:
**RapidAPI Twitter** - 5x tańsze, łatwa migracja
