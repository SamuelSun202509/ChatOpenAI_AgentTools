"""LLM 与 embeddings 工厂（基于 SAP Generative AI Hub）。"""

from __future__ import annotations

import logging
from typing import Any

from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
from gen_ai_hub.proxy.langchain.openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.rate_limiters import InMemoryRateLimiter

logger = logging.getLogger(__name__)


DEFAULT_LLM_MODEL = "gpt-4o"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"


def _default_rate_limiter() -> InMemoryRateLimiter:
    return InMemoryRateLimiter(
        requests_per_second=0.5,
        check_every_n_seconds=0.1,
        max_bucket_size=10,
    )


def create_llm(
    model_name: str = DEFAULT_LLM_MODEL,
    temperature: float = 0.1,
    **kwargs: Any,
) -> ChatOpenAI:
    """构建 ChatOpenAI（经 AI Core 代理）。"""
    proxy_client = get_proxy_client("gen-ai-hub")
    return ChatOpenAI(
        proxy_model_name=model_name,
        proxy_client=proxy_client,
        temperature=temperature,
        rate_limiter=kwargs.pop("rate_limiter", _default_rate_limiter()),
        **kwargs,
    )


def create_embeddings(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    **kwargs: Any,
) -> OpenAIEmbeddings:
    """构建 OpenAIEmbeddings（经 AI Core 代理）。"""
    proxy_client = get_proxy_client("gen-ai-hub")
    return OpenAIEmbeddings(
        proxy_model_name=model_name,
        proxy_client=proxy_client,
        show_progress_bar=kwargs.pop("show_progress_bar", True),
        **kwargs,
    )


def create_llm_and_embeddings(
    llm_model: str = DEFAULT_LLM_MODEL,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> tuple[ChatOpenAI, OpenAIEmbeddings]:
    """一次性构建 LLM + embeddings，复用同一个 proxy client。"""
    return create_llm(llm_model), create_embeddings(embedding_model)
