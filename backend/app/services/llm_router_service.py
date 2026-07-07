from typing import List

from langchain_core.language_models import LanguageModelInput
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.config import Topics, get_settings

settings = get_settings()


class RouterOutput(BaseModel):
    topics: List[Topics] = Field(description="Selected actuall task topics.")


RouterLLM = Runnable[LanguageModelInput, RouterOutput]

llm_router: RouterLLM = ChatOpenAI(
    model=settings.cheap_llm_model,
    temperature=settings.llm_temperature,
).with_structured_output(RouterOutput)