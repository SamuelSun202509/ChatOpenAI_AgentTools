"""SAP HANA Cloud 连接与向量库工厂。"""

from __future__ import annotations

import logging
from typing import Any, Optional

from hdbcli import dbapi

from config import load_hana_credentials

logger = logging.getLogger(__name__)


_connection_cache: Optional[dbapi.Connection] = None


def get_hana_connection(force_new: bool = False) -> dbapi.Connection:
    """获取 HANA 数据库连接（默认带缓存）。

    Args:
        force_new: 如果为 True，忽略缓存重新建立连接。

    Returns:
        已连接的 dbapi.Connection 对象。

    Raises:
        hdbcli.dbapi.Error: 连接失败时由驱动抛出，不再被吞掉。
    """
    global _connection_cache

    if not force_new and _connection_cache is not None:
        try:
            if _connection_cache.isconnected():
                return _connection_cache
        except Exception:
            pass

    creds = load_hana_credentials()

    host = creds["host"]
    port = int(creds.get("port", 443))
    user = creds["user"]
    password = creds["password"]

    logger.info("Connecting to HANA: host=%s port=%s user=%s", host, port, user)

    conn = dbapi.connect(
        address=host,
        port=port,
        user=user,
        password=password,
        encrypt=True,
        autocommit=True,
        sslValidateCertificate=False,
    )

    _connection_cache = conn
    return conn


def get_vectorstore(
    embedding: Any,
    table_name: str,
    **hana_db_kwargs: Any,
):
    """构建 langchain_hana.HanaDB 向量库实例。

    Args:
        embedding: LangChain Embeddings 实例。
        table_name: 存储向量的表名。
        **hana_db_kwargs: 传给 HanaDB 构造函数的其他参数。

    Returns:
        langchain_hana.HanaDB 实例。
    """
    from langchain_hana import HanaDB

    conn = get_hana_connection()
    return HanaDB(
        embedding=embedding,
        connection=conn,
        table_name=table_name,
        **hana_db_kwargs,
    )
