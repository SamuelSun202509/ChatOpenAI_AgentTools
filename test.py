"""连通性自检脚本。

用法：
    python test.py                    # 跑所有检查
    python test.py --skip-hana        # 跳过 HANA（无法访问时）
    python test.py --skip-llm         # 跳过 LLM
    python test.py --skip-rag         # 跳过向量库（依赖 HANA + embeddings）

三件事：
1. 环境检测（local / bas / cf）
2. HANA 连接（isconnected）
3. LLM + embeddings 可用性（尝试一次轻量调用）
"""

from __future__ import annotations

import argparse
import sys
import traceback

from dotenv import load_dotenv

load_dotenv()

from config import ENV, apply_local_proxy
from init_aicore import init_aicore


def check_env() -> None:
    print(f"[env] 检测到运行环境: {ENV}")


def check_hana() -> None:
    from hana_service import get_hana_connection

    print("[hana] 正在连接 HANA ...")
    conn = get_hana_connection()
    is_ok = conn.isconnected()
    print(f"[hana] isconnected() -> {is_ok}")
    if not is_ok:
        raise RuntimeError("HANA 连接建立但 isconnected() 为 False")

    cur = conn.cursor()
    cur.execute("SELECT CURRENT_USER, CURRENT_SCHEMA FROM DUMMY")
    row = cur.fetchone()
    cur.close()
    print(f"[hana] CURRENT_USER={row[0]}, CURRENT_SCHEMA={row[1]}")


def check_llm() -> None:
    from llm_service import create_llm

    print("[llm] 初始化 LLM ...")
    llm = create_llm(model_name="gpt-4o", temperature=0.0)
    print("[llm] 发送一条测试消息 ...")
    resp = llm.invoke("Reply with the single word: pong")
    print(f"[llm] response.content={resp.content!r}")


def check_rag() -> None:
    from hana_service import get_vectorstore
    from llm_service import create_embeddings

    print("[rag] 初始化 embeddings + HanaDB ...")
    embeddings = create_embeddings(model_name="text-embedding-3-large")
    vs = get_vectorstore(embedding=embeddings, table_name="SMOKE_TEST_DOCS")
    print(f"[rag] 向量库对象已创建: {type(vs).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-hana", action="store_true")
    parser.add_argument("--skip-llm", action="store_true")
    parser.add_argument("--skip-rag", action="store_true")
    args = parser.parse_args()

    apply_local_proxy()
    init_aicore()

    checks = [("env", check_env, False)]
    if not args.skip_hana:
        checks.append(("hana", check_hana, False))
    if not args.skip_llm:
        checks.append(("llm", check_llm, False))
    if not args.skip_rag and not args.skip_hana and not args.skip_llm:
        checks.append(("rag", check_rag, False))

    failures: list[str] = []
    for name, fn, _ in checks:
        print(f"\n==== {name.upper()} ====")
        try:
            fn()
            print(f"[{name}] OK")
        except Exception as e:
            print(f"[{name}] FAILED: {e}")
            traceback.print_exc()
            failures.append(name)

    print("\n==== SUMMARY ====")
    if failures:
        print(f"失败的检查: {', '.join(failures)}")
        return 1
    print("全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
