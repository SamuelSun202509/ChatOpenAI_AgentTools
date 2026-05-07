"""Internal knowledge-base search tool (HANA-backed AdvancedRAG).

This tool does NOT synthesize a final answer — it only retrieves and
returns top-K snippets. The agent LLM then writes the final reply with
`[N]` citations itself, which keeps multi-tool flows (Auto mode: KB +
news / weather / wiki) clean.

Side-effect: each call writes the retrieved docs into the module-level
`_LAST_SOURCES` list, which the Streamlit UI pops at the end of every
chat turn to render the References expander beneath the assistant
message. `pop_last_sources()` is the public read-and-clear accessor.
"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.tools import tool

from prompts import build_kb_tool_description
from rag_service import AdvancedRAG, format_docs_as_numbered_context


# ============================================================
# Captured sources for citation display
#
# `make_knowledge_base_tool` writes here on every retrieval; the UI
# pops via `pop_last_sources()` after each turn finishes streaming.
# ============================================================
_LAST_SOURCES: list[Document] = []


def pop_last_sources() -> list[Document]:
    """Pop-and-clear: get the docs retrieved during the current agent turn."""
    docs = list(_LAST_SOURCES)
    _LAST_SOURCES.clear()
    return docs


# ============================================================
# Tool factory
# ============================================================
def make_knowledge_base_tool(rag: AdvancedRAG, kb_display_name: str = ""):
    """Wrap an AdvancedRAG instance into a LangGraph `@tool`.

    Args:
        rag: An already-initialised AdvancedRAG (bound to a specific table).
        kb_display_name: Human-readable KB name (e.g. "SAP BTP") injected
            into the tool description so the tool-selection LLM knows
            which knowledge base it's searching.

    Returns:
        A LangGraph `@tool`-decorated function, ready to register with
        `create_agent(tools=[...])`.
    """

    @tool
    def knowledge_base_search(query: str) -> str:
        """Search the internal knowledge base for relevant documentation snippets.

        Use this tool when the user asks about:
          - Internal product documentation, configuration, or how-to guides
          - Troubleshooting / error diagnosis on internal systems
          - Any question that is likely answered by internal docs rather than the public internet

        The tool returns up to K top-ranked document snippets, each labeled
        `[N] (source: <file>)`. When composing your final answer, cite the
        snippets you used with `[N]` at the end of each factual sentence.

        Args:
            query: A natural-language query. It should be a standalone question
                reflecting the user's intent (the caller is expected to resolve
                any pronouns / references against the full conversation before
                calling this tool).

        Returns:
            A formatted block of numbered snippets, or a "not found" notice.
        """
        docs = rag.retrieve(query)
        _LAST_SOURCES.clear()
        _LAST_SOURCES.extend(docs)
        if not docs:
            return "No relevant snippets found in the knowledge base."
        return format_docs_as_numbered_context(docs)

    # Override the description after @tool has captured __doc__, so we can
    # inject the dynamic `kb_display_name`. (Python stores f-string docstrings
    # as None, so we can't use an f-string as the actual docstring.)
    knowledge_base_search.description = build_kb_tool_description(kb_display_name)
    return knowledge_base_search
