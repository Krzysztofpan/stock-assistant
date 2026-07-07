# Stock Assistant — Backend API

REST API asystenta giełdowego opartego o LangGraph, OpenAI i dane z wielu źródeł MCP (yfinance, finnhub, eodhd).

## Wymagania

- Python 3.12+
- PostgreSQL
- Redis
- [uv](https://docs.astral.sh/uv/) (zalecane)

## Uruchomienie

```bash
cd backend
uv sync --group dev
# uzupełnij backend/.env (patrz sekcja poniżej)
docker compose up -d redis   # z katalogu głównego repozytorium
uv run uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
```

Alternatywnie: `uv run python main.py`

Dokumentacja interaktywna (Swagger): `http://localhost:8000/docs`

## Testy

```bash
cd backend
uv run pytest
```

Wymagają działającej bazy PostgreSQL i Redis (te same połączenia co w `.env`).

## Zmienne środowiskowe

Plik: `backend/.env`

| Zmienna | Wymagana | Domyślnie | Opis |
|---|---|---|---|
| `OPENAI_API_KEY` | tak | — | Klucz API OpenAI |
| `EODHD_API_KEY` | tak | — | Klucz API EODHD (MCP HTTP) |
| `FINNHUB_API_KEY` | tak | — | Klucz API Finnhub (MCP stdio przez `uvx`) |
| `FINNHUB_STORAGE_DIR` | nie | `/tmp/finnhub_storage` | Katalog cache Finnhub MCP |
| `ENABLE_EODHD` | nie | `false` | Włączenie źródła EODHD |
| `ENABLE_YFINANCE` | nie | `true` | Włączenie źródła yfinance |
| `ENABLE_FINNHUB` | nie | `true` | Włączenie źródła finnhub |
| `DATABASE_URL` | tak | — | URL PostgreSQL, np. `postgresql://user:pass@localhost:5432/stock_assistant` |
| `REDIS_HOST` | tak | — | Host Redis |
| `REDIS_PORT` | tak | — | Port Redis |
| `JWT_SECRET` | tak | — | Sekret do podpisywania tokenów JWT |
| `JWT_ALGORITHM` | tak | — | Algorytm JWT, np. `HS256` |
| `ACCESS_TOKEN_EXPIRE_SECONDS` | tak | — | Czas życia tokenu w sekundach |
| `LANGSMITH_API_KEY` | tak | — | Klucz LangSmith (śledzenie LLM) |
| `AGENT_MODEL` | nie | `gpt-4.1-mini` | Model agenta z narzędziami MCP |
| `LLM_MODEL` | nie | `gpt-4o-mini` | Model LLM do generowania odpowiedzi |
| `CHEAP_LLM_MODEL` | nie | `gpt-5-nano` | Tańszy model (router tematów w grafie) |
| `LLM_TEMPERATURE` | nie | `0` | Temperatura LLM |
| `TOKENS_BETWEEN_SUMMARY` | nie | `500` | Próg tokenów przed sumaryzacją |
| `MESSAGES_MAX_LIMIT` | nie | `30` | Maks. limit paginacji wiadomości |
| `CONVERSATIONS_MAX_LIMIT` | nie | `30` | Maks. limit paginacji konwersacji |
| `LANGSMITH_TRACKING` | nie | `true` | Włączenie śledzenia LangSmith |
| `LANGSMITH_PROJECT` | nie | `production-api` | Nazwa projektu LangSmith |
| `APP_ENV` | nie | `development` | Środowisko (`development` / `production`) |
| `LOG_LEVEL` | nie | `INFO` | Poziom logowania |
| `RATE_LIMIT` | nie | `3/minute` | Limit zapytań (obecnie niewykorzystany w kodzie) |
| `CACHE_TTL_SECONDS` | nie | `300` | TTL cache |
| `MAX_RETRIES` | nie | `0` | Maks. liczba retry w grafie agenta |

## Endpointy

### Autoryzacja (`/auth`)

#### `POST /auth/sign-up`

Rejestracja użytkownika.

**Body (JSON):**
```json
{
  "name": "Jan Kowalski",
  "email": "jan@example.com",
  "password": "haslo123",
  "password_repeat": "haslo123"
}
```

- Hasło: min. 8 znaków, co najmniej jedna cyfra.
- Email jest normalizowany (trim + lowercase).

**Odpowiedzi:** `201` — sukces · `400` — email zajęty · `422` — błąd walidacji

---

#### `POST /auth/sign-in`

Logowanie (OAuth2 Password Flow).

**Body (form-urlencoded):**
- `username` — email użytkownika
- `password` — hasło

**Odpowiedź `200`:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

**Odpowiedzi:** `401` — złe dane logowania

Token używaj w nagłówku: `Authorization: Bearer <access_token>`

---

### API (`/api`)

Wszystkie endpointy poniżej wymagają nagłówka `Authorization: Bearer <token>`.

#### `POST /api/chat`

Wysłanie wiadomości do asystenta.

**Body (JSON):**
```json
{
  "message": "Jaka jest cena AAPL?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

- `conversation_id` — UUID; jeśli konwersacja nie istnieje, zostanie utworzona.
- Sumaryzacja konwersacji uruchamiana jest w tle po odpowiedzi.

**Odpowiedź `200`:**
```json
{
  "response": "…",
  "error": null
}
```

Pole `error` wypełniane jest przy błędach po stronie agenta (bez HTTP error).

**Odpowiedzi:** `400` — wiadomość zablokowana przez filtry bezpieczeństwa · `401` — brak/niepoprawny token

---

#### `GET /api/conversations`

Lista konwersacji zalogowanego użytkownika (najnowsze na górze).

**Query params:**
| Param | Typ | Opis |
|---|---|---|
| `limit` | int | Liczba wyników (1–30, domyślnie 20) |
| `before_updated_at` | datetime | Cursor — data aktualizacji |
| `before_id` | UUID | Cursor — ID konwersacji |

Oba parametry cursora muszą być podane razem.

**Odpowiedź `200`:**
```json
{
  "conversations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Cena AAPL",
      "created_at": "2026-06-16T10:00:00Z",
      "updated_at": "2026-06-16T10:05:00Z"
    }
  ],
  "has_more": false
}
```

---

#### `GET /api/conversations/{conversation_id}/messages`

Wiadomości z konwersacji (chronologicznie, od najnowszych okien paginacji).

**Query params:**
| Param | Typ | Opis |
|---|---|---|
| `limit` | int | Liczba wyników (1–30, domyślnie 20) |
| `before_id` | int | Cursor — ID wiadomości |

**Odpowiedź `200`:**
```json
{
  "messages": [
    {
      "id": 1,
      "role": "user",
      "text": "Jaka jest cena AAPL?",
      "created_at": "2026-06-16T10:00:00Z"
    }
  ],
  "has_more": false
}
```

**Odpowiedzi:** `404` — konwersacja nie istnieje lub należy do innego użytkownika

---

## Struktura projektu (skrót)

```
app/
  routes/          # endpointy HTTP
  services/        # logika biznesowa
  memory/          # cache Redis (bufor wiadomości, summary)
  security/        # pipeline bezpieczeństwa wejścia/wyjścia
  graphs/          # LangGraph orchestracji agenta
  agents/          # konfiguracja agenta finansowego
  tortoise/        # modele ORM (PostgreSQL)
  models/          # schematy Pydantic (request/response)
tests/             # testy pytest
```
