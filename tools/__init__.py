"""LangGraph / LangChain tools used by the agent.

Each module exposes either:
  * a `@tool`-decorated function ready to be passed to `create_agent(tools=…)`,
    for stateless tools (e.g. weather, wikipedia), or
  * a factory `make_xxx_tool(...)` / `get_xxx_tool()` that builds a
    parameterized or expensive-to-construct tool (e.g. knowledge-base search,
    Tavily news search).

The single import surface is this package:

    from tools import (
        get_news_search_tool,        # Tavily news (factory; cached)
        get_weather,                 # Open-Meteo current weather
        make_knowledge_base_tool,    # internal HANA RAG (factory)
        pop_last_sources,            # KB references for the UI
        search_wikipedia,            # English Wikipedia summary
    )
"""

from .knowledge_base import make_knowledge_base_tool, pop_last_sources
from .news_search import get_news_search_tool
from .weather import get_weather
from .wikipedia import search_wikipedia

__all__ = [
    "get_news_search_tool",
    "get_weather",
    "make_knowledge_base_tool",
    "pop_last_sources",
    "search_wikipedia",
]
