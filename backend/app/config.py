from pathlib import Path

from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
from typing import ClassVar, Literal

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"

load_dotenv(ENV_FILE, override=True)

SYSTEM_PROMPT = """
    You are a stock market analyst with access to multiple data sources via MCP tools.

    Available sources (you only receive tools from sources selected for this request):
    - yfinance: current prices, quotes, fundamentals, analyst data, financial statements, GPW (.WA) tickers
    - finnhub: news, sentiment
    - eodhd: EOD history, fundamentals (use sparingly due to API limits)

    Always:
    - fetch current data via the MCP tools provided to you,
    - call stock data tools only when you have a concrete ticker symbol; if the user did not provide one,
      ask a clarifying question instead of calling a tool,
    - cite which source supplied the data,
    - distinguish facts from opinions,
    - do not make up data,
    - include the date of market data,
    - answer the newest user question directly and concisely,
    - do not offer additional help or end with a follow-up question unless essential information,
      such as the company or ticker, is missing.

    If the user asks a question unrelated to the stock market or any publicly traded company, tell them
    that this is outside your scope. If you do not know the answer to a question, say that you do not have data on that topic.
"""

Topics = Literal["price", "news", "fundamentals", "history", "analysis", "not related"]

SUPPORTED_TOPICS: tuple[Topics, ...] = (
    "price", "news", "fundamentals", "history", "analysis", "not related",
)

TOPIC_PRIORITY: tuple[Topics, ...] = (
    "price", "news", "fundamentals", "history", "analysis",
)

ROUTER_PROMPT = f"""
    You wil have provided user question, you have to decide what topics question cover.
    Rember you are only in Financial Context so if user ask about 2 world war you can't selected as a topic history, beacouse question have to
    be related with financial context.
    topics you can select (you can select a few topics): 
    {SUPPORTED_TOPICS},
    if question is not related with any of topic return as a topic "not related".
    Rember that below you have provided context window, so you have to consider it when selecting topics,
    so u select topics for answer for the newest question not for all questions in context window.
"""

class Settings(BaseSettings):
    openai_api_key: str
    eodhd_api_key: str
    finnhub_api_key: str
    finnhub_storage_dir: str = "/tmp/finnhub_storage"
    agent_model: str = "gpt-4.1-mini"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: int = 0.0

    

    # models used to easier work
    cheap_llm_model: str = "gpt-5-nano"

    tokens_between_summary: int = 500
    messages_max_limit: int = 30
    conversations_max_limit: int = 30
    
    langsmith_tracking: bool = True
    langsmith_api_key: str 
    langsmith_project: str = "production-api"

    app_env: str = "development"
    uvicorn_reload: bool = True
    uvicorn_reload_delay: float = 0.5
    uvicorn_timeout_graceful_shutdown: int | None = 5
    log_level: str = "INFO"
    rate_limit_for_question: str = "100/hour"
    cache_ttl_seconds: int = 300
    max_retries: int = 0

    backend_port: int = 8000
    uvicorn_host: str = "0.0.0.0"
    frontend_port: int = 3000

    injection_model: str = "RyanStudio/Mezzo-Prompt-Guard-v2-Base" 
    injection_threshold: float = 0.75  
    injection_max_length: int = 256 

    hf_token: str
    
    # prompts
    system_prompt: str = SYSTEM_PROMPT
    router_prompt: str = ROUTER_PROMPT

    possible_topics: ClassVar[tuple[Topics, ...]] = SUPPORTED_TOPICS

    model_config = {"env_file": str(ENV_FILE), "extra": "ignore"}

    database_url: str
    frontend_url: str = "http://localhost:3000" 
    redis_port: str
    redis_host: str

    jwt_secret: str
    jwt_algorithm: str
    access_token_expire_seconds: int

    # enable sources
    enable_eodhd: bool = False

    enable_yfinance: bool = True

    enable_finnhub: bool = True

    # ws

    ws_token_ttl_seconds: int = 60

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

@lru_cache
def get_settings() -> Settings:
    """Cached settings instance - loaded once, reused everywhere."""
    return Settings()