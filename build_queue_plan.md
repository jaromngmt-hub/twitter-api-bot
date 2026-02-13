# BUILD QUEUE SYSTEM - Plan dla wielu projektów

## PROBLEM:
Co 4h może nagromadzić się 5-10 fajnych tweetów z pomysłami na build.
Jak to obsługiwać?

## ROZWIĄZANIE: BUILD QUEUE

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   TWEETY    │────▶│ BUILD QUEUE  │────▶│  BUILDER    │────▶│  GITHUB  │
│  (score 8+) │     │  (Redis DB)  │     │ (1 na raz)  │     │   REPO   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  PRIORYTET   │
                       │  high/medium │
                       └──────────────┘
```

## JAK TO DZIAŁA:

### 1. Dodawanie do kolejki
```
Gdy user kliknie BUILD na Telegramie:
  → Dodaj do build_queue w DB
  → Priority: HIGH (kliknął teraz)
  → Status: pending
  → Estimate cost: $0.50-$2.00
```

### 2. Przetwarzanie kolejki
```
Co godzinę sprawdź queue:
  IF queue not empty AND no build running:
    → Weź NASTĘPNY z kolejki
    → Sprawdź czy stać nas (budżet)
    → IF tak: uruchom build
    → IF nie: czekaj
```

### 3. Priorytetyzacja
```
HIGH (kliknięty przez usera teraz)
  → Builduj w ciągu 1h
  → Max 1 na raz

MEDIUM (pioneer opportunity auto-detected)
  → Builduj jak nie ma HIGH
  → Max 2 dziennie

LOW (reszta)
  → Builduj jak nie ma innych
  → Max 1 dziennie
```

### 4. Ograniczenia budżetowe
```
DAILY_BUILD_BUDGET = $5.00  # limit dziennie

Gdy build się kończy:
  → Sprawdź koszt
  → IF koszt < 80% budżetu:
      → Sprawdź czy kolejka ma coś
      → IF tak: uruchom następny
  → IF koszt > 80% budżetu:
      → STOP, czekaj do jutra
```

### 5. Co z niezbudowanymi?
```
IF tweet w kolejce > 24h:
  → Oznacz jako "expired"
  → Wyślij userowi: "Build wygasł, kliknij ponownie jeśli chcesz"
  → Usuń z kolejki
```

## UI NA TELEGRAM:

```
🛠️ BUILD QUEUE (3 projekty)

1. 🔄 BUILDING NOW (eta: 15 min)
   Solana Trading Bot
   
2. ⏳ QUEUED #1
   Landing Page Generator
   
3. ⏳ QUEUED #2
   AI Newsletter Tool

[🛑 PAUSE] [▶️ NEXT] [❌ CANCEL ALL]
```

## IMPLEMENTACJA - SZYBKIE ROZWIĄZANIE:

### Tabela w SQLite:
```sql
CREATE TABLE build_queue (
    id TEXT PRIMARY KEY,
    tweet_id TEXT,
    username TEXT,
    tweet_text TEXT,
    priority TEXT,  -- high/medium/low
    status TEXT,    -- pending/building/completed/failed/expired
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    cost_estimate REAL,
    actual_cost REAL,
    repo_url TEXT,
    error_message TEXT
);
```

### Proces:
1. User kliknie BUILD → dodaj do queue (status: pending)
2. Scheduler co 30 min sprawdza queue
3. IF pending AND no building → start build (status: building)
4. Po buildzie → update status, repo_url, actual_cost
5. Sprawdź kolejny w queue

## KOSZTY:
- Queue system: $0 (SQLite/Redis już mamy)
- Build cost: $0.50-$2.00 per project
- Max dzienne: $5.00 (3-10 projektów)

## CZY TO NA CIEKAWE?

ZALETY:
✅ Nie tracisz fajnych pomysłów
✅ Kontrola budżetu
✅ User widzi co się dzieje
✅ Możesz pause/resume

WADY:
❌ Trzeba napisać kolejkę
❌ User musi czekać na swoj build

Czy implementować?
