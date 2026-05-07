"""Real-time news search tool (Tavily).

Thin factory that constructs and caches a `langchain_tavily.TavilySearch`
instance configured for recent (past-week) news. The factory is cached
across Streamlit reruns — building a `TavilySearch` is cheap, but
caching avoids redundant validation of `TAVILY_API_KEY`.
"""

from __future__ import annotations

import os

import streamlit as st
from langchain_tavily import TavilySearch


@st.cache_resource(show_spinner=False)
def get_news_search_tool() -> TavilySearch:
    """Return the Tavily news-search tool (`tool name: tavily_search`).

    Raises:
        RuntimeError: if `TAVILY_API_KEY` is not set.
    """
    if not os.environ.get("TAVILY_API_KEY"):
        raise RuntimeError(
            "TAVILY_API_KEY is not set. For local/BAS use a .env file or export "
            "it in the shell; on Cloud Foundry use "
            "`cf set-env <app> TAVILY_API_KEY <key>`."
        )
    return TavilySearch(
        max_results=8,
        topic="general",
        time_range="week",
    )
