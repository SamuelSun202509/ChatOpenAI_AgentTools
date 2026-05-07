"""All prompt templates, centralized in one file.

Grouping prompts together makes it easy to:
  - review wording changes via a single diff
  - A/B test different phrasings
  - translate / localize later without touching application logic

Two groups live here:
  1. **RAG prompts** — used inside `rag_service.AdvancedRAG`
     (condense / variants / answer-synthesis).
  2. **Agent system prompts** — used by `agent_service.build_agent`
     to configure the LangGraph agent's tool-selection behavior
     per search mode.
"""

from __future__ import annotations


# ============================================================
# RAG prompts (used by rag_service.AdvancedRAG)
# ============================================================

CONDENSE_PROMPT = """You are a conversation understanding assistant. Given the chat history below \
and the user's latest question, rewrite the question into a standalone, self-contained question \
that does not depend on prior context.

Rules:
- If the question is already standalone, return it unchanged.
- Preserve key terms (product names, error codes, component names, etc.).
- Output ONLY the rewritten question itself, with no prefix, explanation, or quotes.

Chat history:
{history}

User's latest question: {question}

Standalone rewritten question:"""


VARIANT_PROMPT = """You are a search query generation assistant. Given the user's question, \
generate {n} diverse retrieval query variants to be used against a vector database.

STRICT rules:
- Output one variant per line. No numbering, no quotes, no prefix, no explanation.
- Use ONLY English, OR the user's original question language. Do NOT introduce any other language.
- Variants MUST be meaningfully different from each other, covering angles such as:
  * Technical terminology vs. colloquial phrasing
  * For troubleshooting: symptom / root cause / resolution
  * For how-to: concept explanation / step-by-step instructions / configuration example
  * Different keywords that might match the same topic in the documents
- Preserve key terms verbatim (product names, error codes, component names, API names).
- Keep each variant under 20 words.

User question: {question}

{n} variants:"""


ANSWER_PROMPT = """You are a knowledge-base question answering assistant. Answer the user's question \
based on the document snippets below.

LANGUAGE RULE (MOST IMPORTANT):
- Detect the language of the user's question and answer in EXACTLY that same language.
- If the question is in English, answer in English. If Chinese, answer in Chinese. Never switch to any other language.
- The snippets may be in a different language from the question; that's fine — translate information as needed while keeping technical terms (product names, API names, code snippets) in their original form.

CONTENT RULES:
- Use ONLY information present in the snippets. Do not use outside knowledge or fabricate details.
- Be helpful: even if the snippets only partially answer the question, extract and present whatever relevant information IS available. Do not refuse to answer just because the information is incomplete.
- Only say "No relevant information found in the knowledge base." when the snippets contain NOTHING related to the user's question at all.
- At the end of each factual sentence, cite the supporting snippet(s) using `[N]` format (e.g. `[1]` or `[1][3]`).
- Troubleshooting questions: state the likely cause first, then the resolution steps.
- How-to questions: give a brief concept first, then concrete steps or examples.

Document snippets:
{context}

User question: {question}

Answer (remember: same language as the question):"""


# ============================================================
# Agent system prompts (used by agent_service.build_agent)
#
# The agent is configured differently per search mode. We keep the
# prompt logic as a single function so that callers don't have to know
# about the three variants individually.
# ============================================================

# Presentation rules used whenever the agent has just called `tavily_search`.
# Shared between News-only and Auto mode so both modes produce consistently
# exhaustive output (without this, Auto mode tends to cherry-pick 2–3 results).
_NEWS_PRESENTATION_RULES = (
    "News-result presentation (applies whenever you call `tavily_search`):\n"
    "- Include ALL results returned by the tool (up to 8). Do NOT filter, skip, or "
    "cherry-pick — the user wants the full set.\n"
    "- For EACH result, provide:\n"
    "    1. A clear topic title\n"
    "    2. A comprehensive 3–6 sentence summary (key facts, context, implications, notable figures)\n"
    "    3. The source URL and source name.\n"
    "- Prefer international news/media sources (English, French, Arabic) when applicable."
)


_OFF_TOPIC_NOTICE = (
    "- If the user's question is unrelated to this tool's purpose, briefly explain "
    "that this mode is restricted to a single tool and suggest switching to **Auto** "
    "for general questions. Do NOT call the tool with an irrelevant query."
)


def build_agent_system_prompt(
    mode: str,
    kb_display: str | None,
    today: str,
    *,
    mode_auto: str,
    mode_kb_only: str,
    mode_news_only: str,
    mode_weather_only: str,
    mode_wiki_only: str,
) -> str:
    """Return the system prompt for the given search mode.

    Args:
        mode: one of the mode constants defined in `agent_service`
        kb_display: display name of the knowledge base (None for non-KB modes)
        today: formatted current date string (e.g. "April 20, 2026")
        mode_*: the actual string values of the mode constants (passed in
            to avoid a circular import between `prompts` and `agent_service`).
    """
    base = (
        f"You are a helpful assistant. Today's date is {today}. "
        "Always reply in the same language as the user's question.\n\n"
    )

    if mode == mode_news_only:
        return base + (
            "You have one tool available: `tavily_search` for real-time news search "
            "(the backend is configured to return recent news from the past week).\n"
            "- For news / current-event questions, call `tavily_search`.\n"
            f"{_OFF_TOPIC_NOTICE}\n\n"
            f"{_NEWS_PRESENTATION_RULES}"
        )

    if mode == mode_kb_only:
        return base + (
            f"You have one tool available: `knowledge_base_search` over the "
            f"**{kb_display}** knowledge base.\n"
            "- For EVERY user question, call `knowledge_base_search` first, then answer "
            "based on the returned snippets.\n"
            "- Cite the snippets you used with `[N]` at the end of each factual sentence "
            "(e.g. `...as described in the config guide [1][3]`).\n"
            "- If the snippets do not contain enough information to answer, say so explicitly "
            "— do NOT fall back to general knowledge.\n"
            "- Troubleshooting questions: state the likely cause first, then the resolution steps.\n"
            "- How-to questions: give a brief concept first, then concrete steps or examples."
        )

    if mode == mode_weather_only:
        return base + (
            "You have one tool available: `get_weather` — current weather "
            "(temperature, condition, wind speed) for a specified location, "
            "powered by Open-Meteo.\n"
            "- For any question about current weather / temperature / sky conditions "
            "in a specific place, call `get_weather`.\n"
            "- Present the result as a short, readable paragraph (location, temperature, "
            "condition, wind), not raw JSON.\n"
            f"{_OFF_TOPIC_NOTICE}"
        )

    if mode == mode_wiki_only:
        return base + (
            "You have one tool available: `search_wikipedia` — Wikipedia summary "
            "lookup for a topic, person, place, historical event, or scientific "
            "concept. The tool supports multiple language editions via the "
            "`lang` parameter (\"en\", \"zh\", \"de\", \"fr\", \"ja\", \"ko\", "
            "\"es\", \"ru\"; default \"en\").\n"
            "- For any encyclopedic / factual lookup question, call `search_wikipedia`.\n"
            "- Pick `lang` based on the user's question language: Chinese → "
            "`lang=\"zh\"`, English → `lang=\"en\"`, etc.\n"
            "- If the article isn't found in the chosen language, retry with "
            "`lang=\"en\"` (the English edition has the most articles).\n\n"
            "Output presentation:\n"
            "- Reproduce the **full** `summary` field returned by the tool — do "
            "NOT condense, paraphrase, or pick highlights. Preserve every "
            "paragraph and every fact verbatim. Light formatting (markdown "
            "headings/bullets) is fine, but the wording itself stays intact.\n"
            "- After the verbatim summary, on a new line, cite the source as "
            "`Source: <url>` — write out the full URL string from the `url` field "
            "as plain text. Do NOT wrap it in markdown link syntax like "
            "`[Wikipedia](url)`; the user wants to see the URL itself.\n"
            "- If the article isn't found, briefly say so and suggest a more "
            "specific topic.\n"
            f"{_OFF_TOPIC_NOTICE}"
        )

    # mode_auto (default fallback)
    return base + (
        f"You have four tools:\n"
        f"  1. `knowledge_base_search` — search the internal **{kb_display}** "
        f"knowledge base (product documentation, configuration, troubleshooting).\n"
        f"  2. `tavily_search` — real-time news search (recent news from the past week).\n"
        f"  3. `get_weather` — current weather (temperature, condition, wind) for a "
        f"specific city/place. Two-step under the hood: geocode → forecast.\n"
        f"  4. `search_wikipedia(query, lang)` — Wikipedia summary for a topic, "
        f"person, place, historical event, or scientific concept. Supports "
        f"multiple languages via `lang` (\"en\" default, \"zh\", \"de\", \"fr\", "
        f"\"ja\", \"ko\", \"es\", \"ru\"); pick `lang` to match the question's "
        f"language (Chinese question → `lang=\"zh\"`).\n\n"
        "Tool selection rules:\n"
        "- Internal product / configuration / how-to / error-troubleshooting → "
        "`knowledge_base_search`.\n"
        "- Current events, recent news, or anything time-sensitive → `tavily_search`.\n"
        "- \"What's the weather in <place>?\" / current conditions → `get_weather`.\n"
        "- Encyclopedic / factual lookups about well-known entities (history, "
        "biography, science concepts, geography) → `search_wikipedia`.\n"
        "- If a question has multiple aspects, call ALL the relevant tools and merge "
        "the results (e.g. \"what is X AND latest news about X\" → wiki + tavily).\n"
        "- If `knowledge_base_search` returns no relevant snippets, you may fall back "
        "to `tavily_search` or `search_wikipedia`, whichever is more appropriate.\n"
        "- For general chit-chat or things you already know with certainty (basic "
        "math, common knowledge), you may answer without any tool.\n\n"
        "Knowledge-base-result citation: use `[N]` at the end of each factual sentence.\n\n"
        f"{_NEWS_PRESENTATION_RULES}"
    )


# ============================================================
# Knowledge-base-search tool description (used by agent_service)
# ============================================================

def build_kb_tool_description(kb_display_name: str = "") -> str:
    """Description shown to the agent's tool-selection LLM."""
    kb_hint = f" ({kb_display_name})" if kb_display_name else ""
    return (
        f"Search the internal knowledge base{kb_hint} for relevant documentation snippets.\n\n"
        "Use this tool when the user asks about:\n"
        "  - Internal product documentation, configuration, or how-to guides\n"
        "  - Troubleshooting / error diagnosis on internal systems\n"
        "  - Any question that is likely answered by internal docs rather than the public internet\n\n"
        "The tool returns up to K top-ranked document snippets, each labeled "
        "`[N] (source: <file>)`. When composing your final answer, cite the "
        "snippets you used with `[N]` at the end of each factual sentence."
    )
