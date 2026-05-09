"""Streamlit UI for the RAG + news-search chatbot.

This file is intentionally **UI-only**: all agent wiring, tool factories,
and system prompts live in `agent_service.py`, and the RAG algorithm lives
in `rag_service.py`. That separation keeps each file focused and small:

    app.py            → Streamlit page + sidebar + chat streaming
    agent_service.py  → LangGraph agent + tools + KB registry
    rag_service.py    → Rewrite + Fusion RAG (UI-agnostic)
    prompts.py        → all prompt templates
"""

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from auth_service import validate_authorization_header
from config import ENV, apply_local_proxy


# ============================================================
# Page config (must be the FIRST Streamlit command)
# ============================================================
st.set_page_config(page_title="Chatbot Demo", layout="centered")


# ============================================================
# XSUAA JWT auth gate — runs BEFORE any heavy init.
#
# The backend has a public route, so we must reject any request that does
# not carry a valid `Authorization: Bearer <JWT>` (forwarded by Approuter).
# Doing this first means unauthenticated callers get rejected immediately,
# without paying the cost of `init_aicore()` / agent construction.
#
# On local/BAS runs (no VCAP xsuaa binding) `validate_authorization_header`
# returns a "local-dev" identity automatically.
# ============================================================
def _require_auth() -> "AuthIdentity":  # noqa: F821 — forward ref for readability
    auth_header: str | None = None
    try:
        auth_header = st.context.headers.get("Authorization")
    except Exception:
        auth_header = None

    identity = validate_authorization_header(auth_header)
    if identity is None:
        st.error(
            "🔒 Unauthorized — no valid SSO token was provided.\n\n"
            "This page must be accessed through the company SSO entry point "
            "(the Approuter URL). Please open it from there and sign in."
        )
        st.stop()
    return identity


_identity = _require_auth()


# ============================================================
# Heavy initialization — only runs once the caller is authenticated.
#
# `init_aicore` and `agent_service` are deliberately imported *after*
# the auth gate: they pull in AI Core SDK / LangGraph / HANA clients,
# which take seconds to load and open outbound connections we don't
# want to spend on unauthenticated requests.
# ============================================================
apply_local_proxy()

from init_aicore import init_aicore  # noqa: E402 — intentional post-auth import

init_aicore()

from agent_service import (  # noqa: E402 — intentional post-auth import
    DEFAULT_KB_DISPLAY,
    DEFAULT_MODE,
    KB_DISPLAY_NAMES,
    KNOWLEDGE_BASES,
    MODE_OPTIONS,
    MODES_REQUIRING_KB,
    build_agent,
    pop_last_sources,
)


# ============================================================
# Title + caption (now safe to render — user is authenticated)
# ============================================================
# Hardcoded author tag (the developer who built this demo, not the
# currently signed-in user). Distinct from `_identity.user_name`, which
# changes per session.
_AUTHOR = "UUS1SGH"

st.title("💬 Chatbot Demo")
_who = "local dev" if _identity.is_local_dev else _identity.display_name
st.caption(
    f"AI Core · LangGraph agent · by {_AUTHOR} · env={ENV} · signed in as **{_who}**"
)


# ============================================================
# Sidebar — mode + knowledge base selection
# ============================================================
with st.sidebar:
    st.header("Settings")

    mode = st.radio(
        "Search mode",
        options=MODE_OPTIONS,
        index=MODE_OPTIONS.index(DEFAULT_MODE),
        help=(
            "• **Auto**: the agent autonomously picks one or more of the four tools "
            "based on the question.\n"
            "• **Knowledge base only**: answers come strictly from the selected internal KB.\n"
            "• **News search only**: real-time Tavily news search, no internal documents.\n"
            "• **Weather only**: current weather lookup via Open-Meteo.\n"
            "• **Wikipedia only**: Wikipedia summary lookup (multilingual: en/zh/de/fr/ja/ko/es/ru — agent picks the language to match the question)."
        ),
    )

    kb_required = mode in MODES_REQUIRING_KB
    # Persist the last meaningful KB selection so toggling away→back restores it
    if "kb_display" not in st.session_state:
        st.session_state.kb_display = DEFAULT_KB_DISPLAY

    if kb_required:
        kb_display = st.selectbox(
            "Knowledge base",
            options=KB_DISPLAY_NAMES,
            index=KB_DISPLAY_NAMES.index(st.session_state.kb_display),
            help="Pick the knowledge base the agent should search.",
        )
        st.session_state.kb_display = kb_display
    else:
        # Disabled + empty in any non-KB mode (News / Weather / Wikipedia only)
        st.selectbox(
            "Knowledge base",
            options=[f"(not used in {mode!r} mode)"],
            index=0,
            disabled=True,
            help="The knowledge base is only used in 'Auto' and 'Knowledge base only' modes.",
        )
        kb_display = None

    st.divider()
    if st.button("🧹 Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_seq = st.session_state.get("thread_seq", 0) + 1
        st.rerun()


# ============================================================
# Resolve current agent + thread id
# ============================================================
table_name = KNOWLEDGE_BASES[kb_display] if kb_display else None
agent = build_agent(mode, table_name)

if "thread_seq" not in st.session_state:
    st.session_state.thread_seq = 0
THREAD_ID = f"demo_user_{st.session_state.thread_seq}"


# ============================================================
# Session state
# ============================================================
if "messages" not in st.session_state:
    # Each message: {"role": "user"|"assistant", "content": str, "sources": list[dict]}
    st.session_state.messages = []


# ============================================================
# Rendering helpers
# ============================================================
def _safe_md(content: str) -> str:
    """Sanitize content for Streamlit's markdown renderer.

    Streamlit parses `$...$` as inline LaTeX math (KaTeX), which mangles any
    text containing currency amounts (e.g. "a $300 fine ... a $50,000 fine"
    gets rendered as a math span and overflows the chat bubble). Escaping
    every `$` to `\\$` is the standard markdown way to spell a literal
    dollar sign and keeps prices intact.
    """
    if not content:
        return content
    return content.replace("$", r"\$")


def _render_user(content: str) -> None:
    st.markdown(
        f"""
<div style="display: flex; justify-content: flex-end; margin: 8px 0;">
    <div style="background:#DCF8C6; padding:12px 16px; border-radius:15px; max-width:75%; word-wrap:break-word;">
        {_safe_md(content)}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_assistant(content: str) -> None:
    st.markdown(
        f"""
<div style="display: flex; justify-content: flex-start; margin: 8px 0;">
    <div style="background:#F1F1F1; padding:12px 16px; border-radius:15px; max-width:75%; word-wrap:break-word;">
        {_safe_md(content)}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_sources(sources: list[dict]) -> None:
    """Render the KB citation expander under an assistant message."""
    if not sources:
        return
    with st.expander(f"📚 References ({len(sources)})", expanded=False):
        for i, src in enumerate(sources, start=1):
            meta = src.get("metadata") or {}
            file_name = meta.get("file_name") or meta.get("source") or "unknown"
            source_path = meta.get("source", "")
            start_index = meta.get("start_index", "?")
            preview = src.get("page_content", "")
            st.markdown(
                f"**[{i}] {file_name}**  \n"
                f"<span style='color:#888;font-size:0.85em;'>"
                f"source: {source_path} · start_index: {start_index}</span>",
                unsafe_allow_html=True,
            )
            st.code(
                preview[:1000] + ("…" if len(preview) > 1000 else ""),
                language="markdown",
            )


# ============================================================
# Render history
# ============================================================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        _render_user(msg["content"])
    else:
        _render_assistant(msg["content"])
        _render_sources(msg.get("sources", []))


# ============================================================
# Input + streaming response
# ============================================================
user_input = st.chat_input("Ask me anything…")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    _render_user(user_input)

    status_placeholder = st.empty()
    response_placeholder = st.empty()
    full_response = ""
    is_using_tool = False

    # Defensive: clear any stale sources from previous turn
    pop_last_sources()

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config={"configurable": {"thread_id": THREAD_ID}},
        stream_mode="messages",
    ):
        if not isinstance(chunk, tuple):
            continue

        msg, metadata = chunk
        langgraph_node = metadata.get("langgraph_node", "")

        tool_calls = getattr(msg, "tool_calls", None) or []
        if tool_calls and not is_using_tool:
            first = tool_calls[0]
            name = first.get("name", "") if isinstance(first, dict) else getattr(first, "name", "")
            name_l = name.lower()
            if "knowledge_base" in name_l:
                label = "📚 Searching knowledge base…"
            elif "tavily" in name_l:
                label = "🔍 Searching the news…"
            elif "weather" in name_l:
                label = "🌤️ Checking the weather…"
            elif "wikipedia" in name_l:
                label = "📖 Looking up Wikipedia…"
            elif "search" in name_l:
                label = "🔍 Searching…"
            else:
                label = f"🛠️ Running tool `{name}`…"
            status_placeholder.markdown(f"**{label}**")
            is_using_tool = True

        if langgraph_node == "tools" and not is_using_tool:
            is_using_tool = True
            status_placeholder.markdown("**🛠️ Running tool…**")

        content = getattr(msg, "content", None)
        has_tool_calls = bool(tool_calls)

        # Only stream final-assistant text (not tool outputs / tool_call chunks)
        if (
            content
            and not has_tool_calls
            and langgraph_node != "tools"
            and not content.strip().startswith("{")
        ):
            if is_using_tool:
                status_placeholder.empty()
                is_using_tool = False

            full_response += content
            response_placeholder.markdown(
                f"""
<div style="display: flex; justify-content: flex-start; margin: 8px 0;">
    <div style="background:#F1F1F1; padding:12px 16px; border-radius:15px; max-width:75%; word-wrap:break-word;">
        {_safe_md(full_response)}
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

    status_placeholder.empty()

    # Capture sources used this turn (empty for news-only / unused-KB)
    turn_sources_raw = pop_last_sources()
    turn_sources = [
        {"page_content": d.page_content, "metadata": dict(d.metadata or {})}
        for d in turn_sources_raw
    ]

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response,
            "sources": turn_sources,
        }
    )

    _render_sources(turn_sources)
