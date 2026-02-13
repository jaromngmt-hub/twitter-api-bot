# INFRASTRUCTURE PLAN - Skalowalny Twitter Bot

## ARCHITEKTURA

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SCHEDULER     │────▶│  WORKER QUEUE   │────▶│  AI PROCESSOR   │
│  (co X godzin)  │     │   (Redis/Bull)  │     │  (OpenRouter)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
        ┌───────────────────────────────────────────────┼───────────┐
        │                                               │           │
        ▼                                               ▼           ▼
┌───────────────┐                              ┌──────────────┐ ┌──────────┐
│  Twitter API  │                              │   Discord    │ │ Telegram│
│  (Abstrakcja) │                              │              │ │          │
└───────────────┘                              └──────────────┘ └──────────┘
```

## WARSTWY ABSTRAKCJI

### 1. Twitter API Adapter
```python
class TwitterAdapter(ABC):
    @abstractmethod
    async def get_user_tweets(self, username: str, limit: int) -> List[Tweet]:
        pass
    
    @abstractmethod
    def get_cost_per_request(self) -> float:
        pass

# Implementacje:
# - TwitterAPIioAdapter (obecne)
# - RapidAPIAdapter (5x taniej)
# - ScraperAPIAdapter (15x taniej)
# - OfficialTwitterAdapter (enterprise)
```

### 2. Rate Limiter + Queue
- Redis do kolejki tweetów
- Bull/ARQ do workerów
- Rate limiting per API provider
- Retry logic z backoff

### 3. AI Router (już mamy ✅)
- OpenRouter z fallbackami
- Caching odpowiedzi (Redis)
- Batch processing

### 4. Notification Router
- Discord webhook queue
- Telegram bot queue  
- Retry + dead letter queue

## TECH STACK

| Komponent | Technologia |
|-----------|-------------|
| API | FastAPI |
| Queue | Redis + ARQ |
| DB | PostgreSQL (zamiast SQLite) |
| Cache | Redis |
| Scheduler | APScheduler |
| Workers | Asyncio + ARQ |
| Deploy | Docker + Render/Railway |

## KOSZTY PRZY SKALI

| Element | Obecnie | Po optymalizacji | Przy 10x skali |
|---------|---------|------------------|----------------|
| Twitter API | $40/mc | $8/mc (RapidAPI) | $80/mc |
| AI (OpenRouter) | $30/mc | $15/mc (cache) | $100/mc |
| Redis | $0 | $5/mc | $20/mc |
| PostgreSQL | $0 | $7/mc | $15/mc |
| **RAZEM** | **$70/mc** | **$35/mc** | **$215/mc** |

## IMPLEMENTACJA - KROKI

### Faza 1: Abstrakcja Twitter API
- [ ] Stworzyć `TwitterAdapter` interface
- [ ] Przepisać obecny kod na adapter
- [ ] Dodać RapidAPI adapter
- [ ] Switch w configu

### Faza 2: Queue + Workers  
- [ ] Dodać Redis
- [ ] Zaimplementować ARQ
- [ ] Queue dla tweetów do analizy
- [ ] Queue dla powiadomień

### Faza 3: Cache + Optymalizacja
- [ ] Cache AI odpowiedzi (Redis)
- [ ] Deduplikacja tweetów
- [ ] Batch processing

### Faza 4: Monitoring
- [ ] Metryki (Prometheus/Grafana)
- [ ] Alerty (Discord/Email)
- [ ] Cost tracking

## PRIORYTETY

1. **TERAZ**: Abstrakcja Twitter API (łatwe switchowanie)
2. **ZA TYDZIEŃ**: Queue + Workers (niezawodność)
3. **ZA MIESIĄC**: Cache + monitoring (optymalizacja)

Zaczynamy od Fazy 1?
