"""统一的环境检测与配置加载。

支持三种运行环境：
- local : 本地 Windows / macOS / Linux 开发
- bas   : SAP Business Application Studio
- cf    : SAP BTP Cloud Foundry（通过 VCAP_SERVICES 注入 service binding）
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent

HANA_CONFIG_FILENAME = ".hanadb-config.json"


def detect_env() -> str:
    """检测当前运行环境。"""
    if os.environ.get("VCAP_APPLICATION"):
        return "cf"
    if os.environ.get("WORKSPACE_ID") or os.path.isdir("/home/user/projects"):
        return "bas"
    return "local"


ENV = detect_env()
IS_LOCAL = ENV == "local"
IS_BAS = ENV == "bas"
IS_CF = ENV == "cf"


def apply_local_proxy() -> None:
    """仅在本地（Windows 企业网）需要时应用 HTTP 代理。

    通过环境变量 USE_LOCAL_PROXY=1 显式启用；
    或者设置 LOCAL_PROXY_URL=http://127.0.0.1:3128 来覆盖默认代理地址。
    CF / BAS 环境下无论如何都不会生效。
    """
    if IS_CF or IS_BAS:
        return
    if os.environ.get("USE_LOCAL_PROXY") != "1":
        return

    proxy = os.environ.get("LOCAL_PROXY_URL", "http://127.0.0.1:3128")
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy
    logger.info("Local HTTP proxy applied: %s", proxy)


def _load_hana_from_file() -> Optional[dict[str, Any]]:
    """从 .hanadb-config.json 读取（本地/BAS）。"""
    path = PROJECT_ROOT / HANA_CONFIG_FILENAME
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_hana_from_vcap() -> Optional[dict[str, Any]]:
    """从 VCAP_SERVICES 读取 HANA service binding（Cloud Foundry）。

    兼容以下 service 名称：
    - hana (SAP HANA Cloud schema / hdi-shared plan)
    - hanatrial
    - user-provided（通过 name 包含 'hana' 识别）
    """
    vcap_raw = os.environ.get("VCAP_SERVICES")
    if not vcap_raw:
        return None

    vcap = json.loads(vcap_raw)

    for label in ("hana", "hanatrial"):
        instances = vcap.get(label) or []
        if instances:
            return instances[0].get("credentials") or None

    for instance in vcap.get("user-provided", []) or []:
        name = (instance.get("name") or "").lower()
        if "hana" in name and instance.get("credentials"):
            return instance["credentials"]

    return None


def load_hana_credentials() -> dict[str, Any]:
    """加载 HANA 连接凭证。

    优先顺序：
    1. CF 环境：VCAP_SERVICES
    2. 本地/BAS：.hanadb-config.json

    Returns:
        dict，至少包含 host / port / user / password。
    """
    if IS_CF:
        creds = _load_hana_from_vcap()
        if creds is None:
            raise RuntimeError(
                "运行在 Cloud Foundry，但 VCAP_SERVICES 中未找到 HANA service binding。"
                "请执行 `cf bind-service <app> <hana-instance>` 后重启应用。"
            )
        return creds

    creds = _load_hana_from_file()
    if creds is None:
        raise FileNotFoundError(
            f"未找到 {HANA_CONFIG_FILENAME}（位于项目根目录）。\n"
            "请将 HANA service key 的 JSON 保存为该文件名。"
        )
    return creds
