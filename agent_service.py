"""Agent wiring: knowledge-base registry, mode constants, `build_agent`.

This module is the glue between the RAG layer (`rag_service`, UI-agnostic),
the individual tools (`tools/`), and the LangGraph agent used by the
Streamlit UI. Splitting it out of `app.py` / `rag_service.py` keeps each
of those files focused on its own concern:

  - `rag_service`    — pure retrieval / answer-synthesis algorithms
  - `tools/`         — all `@tool` definitions and tool factories
  - `agent_service`  — KB registry, mode constants, agent builder (this file)
  - `app.py`         — Streamlit UI + streaming chat loop

Dependencies: this module depends on `streamlit` (for `@st.cache_resource`)
because agent / RAG construction is expensive and must be cached across
Streamlit reruns. If you ever need to reuse the agent outside Streamlit,
swap the caches for `functools.lru_cache`.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from llm_service import create_llm
from prompts import build_agent_system_prompt
from rag_service import AdvancedRAG
from tools import (
    get_news_search_tool,
    get_weather,
    make_knowledge_base_tool,
    pop_last_sources,
    search_wikipedia,
)


# ============================================================
# Re-exports — kept for backwards compatibility with `app.py`,
# which imports `pop_last_sources` from `agent_service`.
# ============================================================
__all__ = [
    "DEFAULT_KB_DISPLAY",
    "DEFAULT_MODE",
    "KB_DISPLAY_NAMES",
    "KNOWLEDGE_BASES",
    "MODE_AUTO",
    "MODE_KB_ONLY",
    "MODE_NEWS_ONLY",
    "MODE_WEATHER_ONLY",
    "MODE_WIKI_ONLY",
    "MODE_OPTIONS",
    "MODES_REQUIRING_KB",
    "build_agent",
    "pop_last_sources",
]


# ============================================================
# Knowledge base registry
#   Display name (shown in UI)  ->  HANA table name (used by the RAG)
# Add new knowledge bases here and they'll automatically appear in the
# sidebar dropdown. Keep display names short — they're what the user sees.
# ============================================================
KNOWLEDGE_BASES: dict[str, str] = {
    "SAP BTP": "GIT_DOCS",
    "Dummy":   "SMOKE_TEST_DOCS",
}
KB_DISPLAY_NAMES: list[str] = list(KNOWLEDGE_BASES.keys())
DEFAULT_KB_DISPLAY: str = KB_DISPLAY_NAMES[0]  # "SAP BTP"


# ============================================================
# Search modes
#
# Auto = LLM autonomously picks one or more of the four tools.
# Each "<X> only" mode restricts the agent to a single tool for
# focused demos / debugging.
# ============================================================
MODE_AUTO = "Auto"
MODE_KB_ONLY = "Knowledge base only"
MODE_NEWS_ONLY = "News search only"
MODE_WEATHER_ONLY = "Weather only"
MODE_WIKI_ONLY = "Wikipedia only"
MODE_OPTIONS = [
    MODE_AUTO,
    MODE_KB_ONLY,
    MODE_NEWS_ONLY,
    MODE_WEATHER_ONLY,
    MODE_WIKI_ONLY,
]
DEFAULT_MODE = MODE_AUTO

# Modes in which the KB selector should be enabled (i.e. the agent will
# actually use the KB). Weather-only / Wiki-only / News-only do not.
MODES_REQUIRING_KB = {MODE_AUTO, MODE_KB_ONLY}


# ============================================================
# Factories — cached so switching UI settings is cheap
# ============================================================
@st.cache_resource(show_spinner=False)
def get_llm():
    """Shared chat LLM used by the agent."""
    return create_llm(model_name="gpt-4o", temperature=0.1, max_tokens=8000)


@st.cache_resource(show_spinner="Initializing knowledge base…")
def get_rag(table_name: str) -> AdvancedRAG:
    """Cache one AdvancedRAG instance per HANA table."""
    return AdvancedRAG(table_name=table_name)


# ============================================================
# Agent builder
# ============================================================
@st.cache_resource(show_spinner=False)
def build_agent(mode: str, table_name: str | None) -> Any:
    """Build (and cache) a LangGraph agent for the given mode + KB combination.

    Tool wiring per mode:
      * Auto         → KB + Tavily news + weather + wikipedia (LLM picks)
      * KB-only      → KB only
      * News-only    → Tavily news only
      * Weather-only → get_weather only
      * Wiki-only    → search_wikipedia only

    `table_name` is None for any non-KB mode.
    """
    llm = get_llm()
    today = date.today().strftime("%B %d, %Y")
    kb_display: str | None = None
    tools: list = []

    if mode in MODES_REQUIRING_KB:
        assert table_name, f"mode={mode!r} requires a table_name"
        rag = get_rag(table_name)
        kb_display = next(
            (d for d, t in KNOWLEDGE_BASES.items() if t == table_name),
            table_name,
        )
        tools.append(make_knowledge_base_tool(rag, kb_display_name=kb_display))

    if mode in (MODE_AUTO, MODE_NEWS_ONLY):
        tools.append(get_news_search_tool())

    if mode in (MODE_AUTO, MODE_WEATHER_ONLY):
        tools.append(get_weather)

    if mode in (MODE_AUTO, MODE_WIKI_ONLY):
        tools.append(search_wikipedia)

    system_prompt = build_agent_system_prompt(
        mode=mode,
        kb_display=kb_display,
        today=today,
        mode_auto=MODE_AUTO,
        mode_kb_only=MODE_KB_ONLY,
        mode_news_only=MODE_NEWS_ONLY,
        mode_weather_only=MODE_WEATHER_ONLY,
        mode_wiki_only=MODE_WIKI_ONLY,
    )

    return create_agent(
        tools=tools,
        model=llm,
        system_prompt=system_prompt,
        checkpointer=InMemorySaver(),
    )
