# Stock Assistant

Stock Assistant is an AI-powered web application for researching stocks, markets, and publicly traded companies. Instead of jumping between financial websites and spreadsheets, you ask questions in plain language and get answers grounded in live market data.

The assistant is built for investors, analysts, and anyone curious about the market who wants quick, conversational access to financial information — from current prices and company fundamentals to news, sentiment, and historical trends.

## What it does

Stock Assistant behaves like a knowledgeable market analyst you can chat with. You can:

- **Ask about specific companies** — prices, quotes, financial statements, analyst ratings, and key fundamentals
- **Follow market news and sentiment** — recent headlines and how the market is reacting
- **Explore historical data** — end-of-day history and longer-term trends
- **Keep ongoing conversations** — pick up where you left off, with context preserved across sessions

The AI does not invent numbers. When you ask about a stock, it pulls data from connected financial data providers and cites where the information comes from. If a question falls outside the scope of markets and public companies, the assistant will say so.

## How it works (at a glance)

At a high level, the project consists of three parts:

| Part | Role |
|------|------|
| **Web app** | The interface where you sign in, start conversations, and read responses |
| **API & agent** | Handles authentication, stores conversations, and runs the AI agent that answers your questions |
| **Data sources** | External market data providers (e.g. Yahoo Finance, Finnhub, EODHD) that supply real-time and historical information |

When you send a message, the system routes your question to the right kind of data, fetches what it needs, and streams the answer back to you in the chat.

## Who is this for?

This repository is a full-stack application — not a library or a single script. It is meant for people who want to:

- Run their own instance of an AI stock research assistant
- Experiment with conversational financial analysis
- Extend or customize how market data is combined with language models

You do not need to read the source code to understand the idea: **a private, chat-based research tool for the stock market, powered by AI and live data.**

## Getting started

To run the project locally you will need:

1. **Docker** (recommended) — the easiest way to start all services together
2. **A `.env` file** — copy `.env.example` to `.env` in the repository root and fill in the required values
3. **API keys** for:
   - **OpenAI** — powers the AI agent
   - **Finnhub** — news and sentiment data
   - **EODHD** — optional; historical and fundamental data
   - **Supabase / PostgreSQL** — user accounts and conversation history
   - **LangSmith** — optional; tracing and observability for the AI pipeline

Then from the repository root:

```bash
cp .env.example .env
# edit .env with your keys
docker compose up
```

The web app will be available at `http://localhost:3000` and the API at `http://localhost:8000` (ports are configurable in `.env`).

For more detailed setup and API documentation, see the README files in the `backend/` and `frontend/` directories.

## Important note

Stock Assistant is a **research and information tool**. It does not provide personalized investment advice, execute trades, or guarantee the accuracy of third-party data. Always verify critical information independently and consult a qualified financial professional before making investment decisions.

## License

See the repository for license information.
