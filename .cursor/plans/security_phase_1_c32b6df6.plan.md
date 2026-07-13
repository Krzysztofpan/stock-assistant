---
name: Security Phase 1
overview: "Wdrożenie Fazy 1 ulepszonego security: DeBERTa jako gate na prompt injection (pre-graph), TopicRouterService zastępujący bezpośredni LLM router w select_topics, oraz Presidio zamiast regex PII na input/output."
todos:
  - id: deps-config
    content: Dodać zależności (transformers, torch, presidio, spacy) i nowe ustawienia w config.py
    status: completed
  - id: routing-models
    content: Utworzyć backend/app/models/routing.py z SafetyVerdict i TopicRoutingResult
    status: in_progress
  - id: presidio-pii
    content: Przepisać PIIDetector na Presidio zachowując interfejs detect/mask
    status: pending
  - id: injection-classifier
    content: Utworzyć InjectionClassifier (DeBERTa) z lazy load i asyncio.to_thread
    status: pending
  - id: topic-router-service
    content: "Utworzyć TopicRouterService: check_safety + resolve_topics (rules → LLM)"
    status: pending
  - id: chat-service-refactor
    content: "Refactor chat_service: parallel safety gate + ensure_exists przed add_message"
    status: pending
  - id: graph-wiring
    content: Podpiąć TopicRouterService w stock_assistant_graph, stock_assistant.py i app.py
    status: pending
  - id: tests
    content: Dodać testy topic_router, presidio PII; zaktualizować conftest i test_stock_assistant_graph
    status: pending
isProject: false
---

# Plan: Security Faza 1 + Presidio

## Cel

Zastąpić słabe regexy dwiema warstwami:
- **Pre-graph**: Tier 0 regex (szybki filtr) + Presidio PII + DeBERTa injection gate
- **In-graph**: `TopicRouterService` (rules → LLM fallback) zamiast bezpośredniego `llm_router.ainvoke` w `select_topics`

Bez dodatkowego LLM calla na security. Topic BERT (Faza 2) pozostaje za flagą `enable_topic_bert=False`.

```mermaid
flowchart TD
    req[ChatRequest] --> tier0[Tier0: InputSanitizer regex]
    tier0 -->|blocked| err[InputBlockedError]
    tier0 --> presidio[Presidio PII mask]
    presidio --> parallel["asyncio.gather"]
    parallel --> bert[InjectionClassifier DeBERTa]
    parallel --> db[session.ensure_exists]
    bert -->|unsafe| err
    bert --> save[add_message + get_context]
    save --> graph[LangGraph select_topics]
    graph --> rules{rule match?}
    rules -->|yes| agent[choose_sources → agent]
    rules -->|no| llm[cheap LLM router fallback]
    llm --> agent
```

## Zakres plików

### Nowe pliki

| Plik | Odpowiedzialność |
|------|------------------|
| [`backend/app/models/routing.py`](backend/app/models/routing.py) | `SafetyVerdict`, `TopicRoutingResult`, typy `RiskType` / `RoutingSource` |
| [`backend/app/core/security/injection_classifier.py`](backend/app/core/security/injection_classifier.py) | Wrapper DeBERTa (`protectai/deberta-v3-base-prompt-injection-v2`), lazy load, `asyncio.to_thread` |
| [`backend/app/services/topic_router_service.py`](backend/app/services/topic_router_service.py) | `check_safety()` pre-graph + `resolve_topics()` in-graph |
| [`backend/tests/test_topic_router_service.py`](backend/tests/test_topic_router_service.py) | Testy routingu i safety gate |
| [`backend/tests/test_pii_detector.py`](backend/tests/test_pii_detector.py) | Testy Presidio PII (email, phone, karta) |

### Modyfikowane pliki

| Plik | Zmiana |
|------|--------|
| [`backend/pyproject.toml`](backend/pyproject.toml) | Dodać: `transformers`, `torch`, `presidio-analyzer`, `presidio-anonymizer`, `spacy` |
| [`backend/app/config.py`](backend/app/config.py) | `injection_threshold`, `enable_topic_bert`, `topic_bert_threshold` (na przyszłość) |
| [`backend/app/core/security/PII_detector.py`](backend/app/core/security/PII_detector.py) | Zamiana regex → Presidio; zachować interfejs `detect()` / `mask()` |
| [`backend/app/core/security/output_validator.py`](backend/app/core/security/output_validator.py) | Bez zmian API — korzysta z nowego `PIIDetector` |
| [`backend/app/core/security/security_pipeline.py`](backend/app/core/security/security_pipeline.py) | Bez zmian API — Tier 0 + Presidio |
| [`backend/app/services/chat_service.py`](backend/app/services/chat_service.py) | Wstrzyknięcie `TopicRouterService`, parallel safety + `ensure_exists` |
| [`backend/app/graphs/stock_assistant_graph.py`](backend/app/graphs/stock_assistant_graph.py) | `TopicRouterService` zamiast `llm_router` w `select_topics` |
| [`backend/app/services/stock_assistant.py`](backend/app/services/stock_assistant.py) | Przekazanie `topic_router` do `StockAssistantGraph` |
| [`backend/app/app.py`](backend/app/app.py) | Inicjalizacja singletonów przy starcie |
| [`backend/tests/conftest.py`](backend/tests/conftest.py) | Mock `TopicRouterService` w fixture `client` |
| [`backend/tests/test_stock_assistant_graph.py`](backend/tests/test_stock_assistant_graph.py) | Zamiana `mock_llm_router` → `mock_topic_router` |

---

## Krok 1: Zależności i config

**`pyproject.toml`** — dodać pakiety ML i Presidio.

**`config.py`** — nowe ustawienia:
```python
injection_threshold: float = 0.85
injection_model: str = "protectai/deberta-v3-base-prompt-injection-v2"
enable_topic_bert: bool = False          # hook na Fazę 2
topic_bert_threshold: float = 0.70
```

**SpaCy model** — Presidio wymaga `en_core_web_lg` (lub `sm` na dev). Dodać do README/komentarza w `app.py` lifespan: `python -m spacy download en_core_web_lg`. Model pobierany raz przy setupie, nie per request.

---

## Krok 2: Modele routingu

Nowy [`backend/app/models/routing.py`](backend/app/models/routing.py):

```python
class SafetyVerdict(BaseModel):
    is_safe: bool
    risk: Literal["none", "prompt_injection", ...]
    confidence: float

class TopicRoutingResult(BaseModel):
    topics: list[Topics]
    source: Literal["rules", "bert", "llm"]
```

Osobne modele dla safety i routingu — nie jedna klasa wyjściowa.

---

## Krok 3: Presidio zamiast regex PII

Przepisać [`PII_detector.py`](backend/app/core/security/PII_detector.py) zachowując ten sam kontrakt:

```python
def detect(self, text: str) -> dict[str, list[str]]  # klucze: email, phone, ssn, credit_card
def mask(self, text: str) -> str
```

Implementacja:
- `AnalyzerEngine` z recognizerami: `EMAIL_ADDRESS`, `PHONE_NUMBER`, `CREDIT_CARD`, `US_SSN`
- `AnonymizerEngine` z operatorami replace → te same maski co dziś (`[EMAIL REDACTED]` itd.)
- `detect()` mapuje entity Presidio na istniejące klucze w `SecurityPipeline` notes
- Inferencja przez `asyncio.to_thread` jeśli wołane async (opcjonalnie — na razie sync w `check_input` jest OK, ~50ms)

`SecurityPipeline` i `OutputValidator` **nie zmieniają sygnatury** — tylko lepsza implementacja pod spodem.

---

## Krok 4: InjectionClassifier (DeBERTa)

Nowy [`injection_classifier.py`](backend/app/core/security/injection_classifier.py):

- Lazy load pipeline przy pierwszym użyciu (nie blokuj startup jeśli model się pobiera)
- `async classify(text: str) -> SafetyVerdict` — `asyncio.to_thread` na sync `pipeline()`
- Truncate input do 512 tokenów
- Singleton via `get_injection_classifier()` (`@lru_cache`)
- `@traceable(name="injection_classify")` dla LangSmith

Regex injection w [`input_sanitizer.py`](backend/app/core/security/input_sanitizer.py) **zostaje** jako Tier 0 (<1ms, łapie oczywiste przypadki). DeBERTa łapie resztę — defense in depth.

---

## Krok 5: TopicRouterService

Nowy [`topic_router_service.py`](backend/app/services/topic_router_service.py) — zastępuje bezpośrednie użycie [`llm_router_service.py`](backend/app/services/llm_router_service.py) w grafie:

**`check_safety(user_message)`** — wołane z `chat_service` pre-graph:
```python
return await self.injection.classify(user_message)
```

**`resolve_topics(user_message, messages)`** — wołane z `select_topics`:
1. `match_topics_from_rules()` → return `source="rules"` (bez LLM)
2. Jeśli `enable_topic_bert` → BERT (Faza 2, na razie pominięte)
3. Fallback: `llm_router.ainvoke()` z istniejącym `router_prompt` + context → `source="llm"`

Logika przeniesiona z obecnego [`select_topics`](backend/app/graphs/stock_assistant_graph.py) (linie 129–148) do serwisu — graf tylko deleguje.

---

## Krok 6: Refactor ChatService (pre-graph gate)

[`chat_service.py`](backend/app/services/chat_service.py) — nowy konstruktor z `topic_router: TopicRouterService`:

```python
# 1. Tier 0 + Presidio (sync)
is_allowed, cleaned, _ = self.security.check_input(request.message)
if not is_allowed: raise InputBlockedError()

session = ConversationSession(...)

# 2. Równolegle: DeBERTa + DB
safety, _ = await asyncio.gather(
    self.topic_router.check_safety(cleaned),
    session.ensure_exists(),
)
if not safety.is_safe: raise InputBlockedError()

# 3. Dopiero teraz zapis wiadomości
await session.add_message("user", cleaned)
```

Kluczowe: injection check **przed** `add_message` — zablokowana wiadomość nie trafia do DB.

---

## Krok 7: Refactor grafu i wiring

**[`stock_assistant_graph.py`](backend/app/graphs/stock_assistant_graph.py)**:
- `__init__(agent, llm, topic_router: TopicRouterService)` zamiast `llm_router`
- `select_topics` → `await self.topic_router.resolve_topics(user_question, state["messages"])`

**[`stock_assistant.py`](backend/app/services/stock_assistant.py)**:
- `create_stock_assistant(topic_router)` przyjmuje router z zewnątrz

**[`app.py`](backend/app/app.py)** — lifespan:
```python
topic_router = TopicRouterService(
    injection_classifier=get_injection_classifier(),
    llm_router=llm_router,
)
chat_service = ChatService(security=..., topic_router=topic_router, ...)
stock_assistant = await create_stock_assistant(topic_router)
```

---

## Krok 8: Testy

| Test | Co weryfikuje |
|------|---------------|
| `test_match_topics_from_rules` | Bez zmian — regresja rules |
| `test_rules_bypass_llm` | Pytanie z rules → `llm_router` nie wołany |
| `test_ambiguous_question_uses_llm` | Brak rule match → LLM fallback |
| `test_injection_blocked_pre_graph` | DeBERTa mock → `InputBlockedError`, brak `add_message` |
| `test_tier0_regex_still_blocks` | Oczywisty injection regex → block bez DeBERTa |
| `test_presidio_masks_email` | `"kontakt jan@test.com"` → `[EMAIL REDACTED]` |
| `test_out_of_scope_skips_agent` | Update mocków na `TopicRouterService` |

Wszystkie testy używają mocków dla DeBERTa i Presidio — bez pobierania modeli w CI.

---

## Poza zakresem tego planu (kolejne iteracje)

- **Topic BERT classifier** (Faza 2) — wymaga datasetu i fine-tune; hook `enable_topic_bert` gotowy
- **Output filter w trakcie streamu** — dziś `check_output` działa po streamie ([`chat_service.py:65-79`](backend/app/services/chat_service.py)); PII może przejść do klienta przed maskowaniem
- **Redis cache odpowiedzi** — osobny task z `actual_task`

---

## Ryzyka i mitigacje

| Ryzyko | Mitygacja |
|--------|-----------|
| Pierwszy start pobiera ~300MB model DeBERTa | Lazy load; opcjonalnie pre-download w Docker build |
| Presidio wolniejsze niż regex (~50ms) | Akceptowalne; nadal szybsze niż LLM |
| False positives DeBERTa na język giełdowy | Tier 0 + threshold 0.85; loguj `confidence` w LangSmith do kalibracji |
| SpaCy model nie zainstalowany | Jawny błąd przy starcie z czytelnym komunikatem |
