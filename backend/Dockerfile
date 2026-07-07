FROM python:3.12-slim

ARG BACKEND_PORT=8000
ARG UVICORN_HOST=0.0.0.0

ENV BACKEND_PORT=${BACKEND_PORT}
ENV UVICORN_HOST=${UVICORN_HOST}

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY . .

# MCP serwery uruchamiane przez uvx w runtime — instalujemy je przy buildzie
RUN uv tool install yfinance-market-mcp \
    && uv tool install --from "git+https://github.com/cfdude/mcp-finnhub" mcp-finnhub

EXPOSE ${BACKEND_PORT}

CMD ["uv", "run", "main.py"]
