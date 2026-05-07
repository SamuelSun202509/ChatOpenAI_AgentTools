"""Advanced RAG: Query Rewrite + RAG Fusion.

Pipeline:
    history + question
        → 1. Condense    (fold multi-turn context into a standalone question)
        → 2. Variants    (generate N diverse retrieval query variants)
        → 3. Retrieve    (vector-search each variant independently)
        → 4. RRF         (Reciprocal Rank Fusion to merge + dedupe)
        → 5. Synthesize  (generate a cited answer from the top-K docs)

This module is UI-agnostic. The Streamlit / LangGraph glue lives in
`agent_service.py`; prompt templates live in `prompts.py`.

CLI usage (standalone test):
    python rag_service.py "SSO login returns 403"
    python rag_service.py --verbose "page unresponsive after deploy"
    python rag_service.py --table GIT_DOCS --verbose "how to configure subaccount"
    python rag_service.py --interactive          # multi-turn chat mode

Programmatic usage:
    from rag_service import AdvancedRAG
    rag = AdvancedRAG(table_name="GIT_DOCS")
    answer, sources = rag.answer("how to configure subaccount")
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field

from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv()

from hana_service import get_vectorstore
from init_aicore import init_aicore
from llm_service import create_embeddings, create_llm
from prompts import ANSWER_PROMPT, CONDENSE_PROMPT, VARIANT_PROMPT

logger = logging.getLogger(__name__)


# ============================================================
# 可调参数（也可以通过 AdvancedRAG 构造函数覆盖）
# ============================================================
DEFAULT_TABLE_NAME = "GIT_DOCS"
DEFAULT_N_VARIANTS = 4
DEFAULT_K_RETRIEVE = 5
DEFAULT_K_FINAL = 8
DEFAULT_RRF_K = 60
DEFAULT_HISTORY_TURNS = 4


# ============================================================
# 数据结构
# ============================================================
@dataclass
class RAGTrace:
    """调试追踪信息，verbose=True 时可以打印出来看中间步骤。"""
    original_question: str = ""
    condensed_question: str = ""
    variants: list[str] = field(default_factory=list)
    per_variant_hits: list[list[Document]] = field(default_factory=list)
    fused_docs: list[Document] = field(default_factory=list)
    fused_scores: dict[str, float] = field(default_factory=dict)


# ============================================================
# 核心工具函数
# ============================================================
def _dedup_key(doc: Document) -> str:
    """用 source + start_index 组合作为 chunk 的唯一标识。"""
    meta = doc.metadata or {}
    src = meta.get("source") or meta.get("file_path") or "unknown"
    start = meta.get("start_index", 0)
    return f"{src}::{start}"


def reciprocal_rank_fusion(
    result_lists: list[list[Document]],
    k: int = DEFAULT_RRF_K,
    top_k: int = DEFAULT_K_FINAL,
) -> tuple[list[Document], dict[str, float]]:
    """Reciprocal Rank Fusion。

    对每个 chunk 在每个检索结果中的名次计算 1/(rank + k)，全部相加后排序。
    同一 chunk 在多个变体里都出现 → 分数累加；越靠前分越高。

    Returns:
        (融合后的文档列表, {dedup_key: score}).
    """
    scores: dict[str, float] = {}
    doc_by_key: dict[str, Document] = {}

    for docs in result_lists:
        for rank, doc in enumerate(docs):
            key = _dedup_key(doc)
            scores[key] = scores.get(key, 0.0) + 1.0 / (rank + k)
            if key not in doc_by_key:
                doc_by_key[key] = doc

    ranked_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]
    ranked_docs = [doc_by_key[k] for k in ranked_keys]
    return ranked_docs, {k: scores[k] for k in ranked_keys}


def _format_history(history: list[tuple[str, str]], max_turns: int) -> str:
    """把历史对话格式化成可读文本。

    Args:
        history: [(role, content), ...]，role 是 'user' 或 'assistant'
        max_turns: 最多保留的轮数（一轮 = user + assistant 两条）
    """
    if not history:
        return "(no prior conversation)"
    recent = history[-(max_turns * 2):]
    lines = []
    for role, content in recent:
        prefix = "User" if role == "user" else "Assistant"
        lines.append(f"{prefix}: {content}")
    return "\n".join(lines)


def format_docs_as_numbered_context(docs: list[Document]) -> str:
    """Format top-K docs as a numbered `[N] (source: ...) ...` context block.

    Used by the internal answer-synthesis step AND by the LangGraph tool
    wrapper in `agent_service`, so it's part of the public API.
    """
    blocks = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        src = meta.get("file_name") or meta.get("source") or "unknown"
        blocks.append(
            f"[{i}] (source: {src})\n{doc.page_content.strip()}"
        )
    return "\n\n".join(blocks)


# ============================================================
# AdvancedRAG 主类
# ============================================================
class AdvancedRAG:
    """封装 Rewrite + Fusion RAG 的完整流程。"""

    def __init__(
        self,
        table_name: str = DEFAULT_TABLE_NAME,
        *,
        llm_model: str = "gpt-4o",
        embedding_model: str = "text-embedding-3-large",
        n_variants: int = DEFAULT_N_VARIANTS,
        k_retrieve: int = DEFAULT_K_RETRIEVE,
        k_final: int = DEFAULT_K_FINAL,
        rrf_k: int = DEFAULT_RRF_K,
        history_turns: int = DEFAULT_HISTORY_TURNS,
    ):
        self.table_name = table_name
        self.n_variants = n_variants
        self.k_retrieve = k_retrieve
        self.k_final = k_final
        self.rrf_k = rrf_k
        self.history_turns = history_turns

        logger.info(
            "Initializing AdvancedRAG: table=%s, n_variants=%d, k_retrieve=%d, k_final=%d",
            table_name, n_variants, k_retrieve, k_final,
        )

        # 共享 LLM（用于 condense + variant + answer，都用同一个 model 即可）
        self.llm = create_llm(model_name=llm_model, temperature=0.1)
        self.embeddings = create_embeddings(
            model_name=embedding_model,
            show_progress_bar=False,  # CLI 模式下不要进度条污染输出
        )
        self.vectorstore = get_vectorstore(
            embedding=self.embeddings,
            table_name=table_name,
        )

    # ----------------- Step 1: Condense -----------------
    def _condense(self, question: str, history: list[tuple[str, str]]) -> str:
        """把历史对话 + 当前问题合并成独立问题。"""
        if not history:
            return question
        prompt = CONDENSE_PROMPT.format(
            history=_format_history(history, self.history_turns),
            question=question,
        )
        resp = self.llm.invoke(prompt)
        return resp.content.strip()

    # ----------------- Step 2: Generate variants -----------------
    def _generate_variants(self, question: str) -> list[str]:
        """LLM 生成 N 个检索查询变体。原问题也作为一个变体。"""
        prompt = VARIANT_PROMPT.format(question=question, n=self.n_variants)
        resp = self.llm.invoke(prompt)
        variants = [
            line.strip().lstrip("0123456789.-) ").strip()
            for line in resp.content.split("\n")
            if line.strip()
        ]
        variants = [v for v in variants if len(v) >= 2][: self.n_variants]

        # 原问题也加进去做一次检索，保底
        if question not in variants:
            variants = [question] + variants
        return variants

    # ----------------- Step 3: Retrieve per variant -----------------
    def _retrieve_per_variant(
        self, variants: list[str]
    ) -> list[list[Document]]:
        """对每个变体独立做向量检索。"""
        all_hits: list[list[Document]] = []
        for v in variants:
            try:
                hits = self.vectorstore.similarity_search(v, k=self.k_retrieve)
            except Exception as e:
                logger.warning("Retrieval failed for variant %r: %s", v, e)
                hits = []
            all_hits.append(hits)
        return all_hits

    # ----------------- Step 4: Answer synthesis -----------------
    def _synthesize_answer(
        self, question: str, docs: list[Document]
    ) -> str:
        if not docs:
            return "No relevant information found in the knowledge base."
        prompt = ANSWER_PROMPT.format(
            context=format_docs_as_numbered_context(docs),
            question=question,
        )
        resp = self.llm.invoke(prompt)
        return resp.content.strip()

    # ----------------- 仅检索（供 LangGraph tool 使用）-----------------
    def retrieve(
        self,
        question: str,
        *,
        return_trace: bool = False,
    ) -> list[Document] | tuple[list[Document], RAGTrace]:
        """只做"变体生成 + 多路检索 + RRF"，不调用 LLM 生成答案。

        用于作为 LangGraph agent 的 tool：agent 本身会把返回的文档片段
        融进它的回答中，避免 RAG 再做一次合成导致双重总结。

        Note: 这里不做 condense —— agent 在调用 tool 时传入的 query 已经是
        基于完整对话理解后构造的独立 query，无需再次改写。

        Args:
            question: 用户问题（通常是 agent 基于完整历史构造的 tool query）
            return_trace: 是否返回调试追踪

        Returns:
            list[Document] 或 (list[Document], trace)
        """
        trace = RAGTrace(original_question=question, condensed_question=question)

        variants = self._generate_variants(question)
        trace.variants = variants

        per_variant = self._retrieve_per_variant(variants)
        trace.per_variant_hits = per_variant

        fused_docs, fused_scores = reciprocal_rank_fusion(
            per_variant, k=self.rrf_k, top_k=self.k_final
        )
        trace.fused_docs = fused_docs
        trace.fused_scores = fused_scores

        if return_trace:
            return fused_docs, trace
        return fused_docs

    # ----------------- 主入口（带答案合成，供 CLI / 直接调用）-----------------
    def answer(
        self,
        question: str,
        history: list[tuple[str, str]] | None = None,
        *,
        return_trace: bool = False,
    ) -> tuple[str, list[Document]] | tuple[str, list[Document], RAGTrace]:
        """完整的 Rewrite + Fusion RAG 流程（包含 condense + 答案合成）。

        Args:
            question: 用户当前问题
            history: [(role, content), ...]，可选的多轮对话历史
            return_trace: 是否返回调试追踪信息

        Returns:
            (answer_text, source_docs) 或 (answer_text, source_docs, trace)
        """
        trace = RAGTrace(original_question=question)

        condensed = self._condense(question, history or [])
        trace.condensed_question = condensed

        variants = self._generate_variants(condensed)
        trace.variants = variants

        per_variant = self._retrieve_per_variant(variants)
        trace.per_variant_hits = per_variant

        fused_docs, fused_scores = reciprocal_rank_fusion(
            per_variant, k=self.rrf_k, top_k=self.k_final
        )
        trace.fused_docs = fused_docs
        trace.fused_scores = fused_scores

        answer_text = self._synthesize_answer(condensed, fused_docs)

        if return_trace:
            return answer_text, fused_docs, trace
        return answer_text, fused_docs


# ============================================================
# CLI
# ============================================================
def _print_trace(trace: RAGTrace) -> None:
    """verbose 模式下打印完整中间步骤。"""
    print("\n" + "=" * 70)
    print("ORIGINAL QUESTION:")
    print(f"  {trace.original_question}")

    if trace.condensed_question != trace.original_question:
        print("\nCONDENSED (Rewrite):")
        print(f"  {trace.condensed_question}")

    print(f"\nGENERATED {len(trace.variants)} VARIANTS:")
    for i, v in enumerate(trace.variants, 1):
        print(f"  [{i}] {v}")

    print("\nPER-VARIANT RETRIEVAL (top docs):")
    for i, (variant, hits) in enumerate(
        zip(trace.variants, trace.per_variant_hits), 1
    ):
        print(f"\n  Variant [{i}] {variant!r} -> {len(hits)} docs:")
        for j, doc in enumerate(hits[:3], 1):  # 只打前 3 个
            src = (doc.metadata or {}).get("file_name", "?")
            preview = doc.page_content[:80].replace("\n", " ")
            print(f"    {j}. [{src}] {preview}...")

    print("\nRRF FUSED (top-K after dedup):")
    for i, doc in enumerate(trace.fused_docs, 1):
        key = _dedup_key(doc)
        score = trace.fused_scores.get(key, 0.0)
        src = (doc.metadata or {}).get("file_name", "?")
        preview = doc.page_content[:80].replace("\n", " ")
        print(f"  [{i}] score={score:.4f}  [{src}]  {preview}...")
    print("=" * 70 + "\n")


def _print_answer(answer: str, docs: list[Document]) -> None:
    print("\n" + "─" * 70)
    print("ANSWER:")
    print(answer)
    print("\n" + "─" * 70)
    print("REFERENCES:")
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata or {}
        src = meta.get("source", "?")
        start = meta.get("start_index", "?")
        print(f"  [{i}] {src} (start_index={start})")
    print("─" * 70 + "\n")


def _cli_single(rag: AdvancedRAG, question: str, verbose: bool) -> None:
    answer, docs, trace = rag.answer(question, return_trace=True)
    if verbose:
        _print_trace(trace)
    _print_answer(answer, docs)


def _cli_interactive(rag: AdvancedRAG, verbose: bool) -> None:
    print("\n多轮对话模式（输入 'quit' 或 Ctrl-C 退出）\n")
    history: list[tuple[str, str]] = []
    while True:
        try:
            q = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q.lower() in ("quit", "exit", "q"):
            break

        answer, docs, trace = rag.answer(q, history=history, return_trace=True)
        if verbose:
            _print_trace(trace)
        _print_answer(answer, docs)

        history.append(("user", q))
        history.append(("assistant", answer))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Advanced RAG (Rewrite + Fusion) over HANA vector store."
    )
    parser.add_argument("question", nargs="?", help="单次提问；不填则进入交互模式")
    parser.add_argument(
        "--table", "-t", default=DEFAULT_TABLE_NAME, help="HANA 表名"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="强制多轮对话模式"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="打印中间步骤"
    )
    parser.add_argument(
        "--n-variants", type=int, default=DEFAULT_N_VARIANTS, help="变体数量"
    )
    parser.add_argument(
        "--k-retrieve", type=int, default=DEFAULT_K_RETRIEVE, help="每变体检索数"
    )
    parser.add_argument(
        "--k-final", type=int, default=DEFAULT_K_FINAL, help="RRF 后保留数"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    init_aicore()

    rag = AdvancedRAG(
        table_name=args.table,
        n_variants=args.n_variants,
        k_retrieve=args.k_retrieve,
        k_final=args.k_final,
    )

    if args.interactive or not args.question:
        _cli_interactive(rag, args.verbose)
    else:
        _cli_single(rag, args.question, args.verbose)

    return 0


if __name__ == "__main__":
    sys.exit(main())
