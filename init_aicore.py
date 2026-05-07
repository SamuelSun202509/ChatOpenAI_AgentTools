"""SAP Generative AI Hub / AI Core bootstrap.

Populates the environment variables required by `gen_ai_hub` so that the
LangChain / embeddings clients can authenticate against AI Core. The
bootstrap transparently handles three deployment scenarios:

  1. **Local (config file)** — `~/.aicore/config.json` already on disk.
     Nothing to do: the `gen_ai_hub` SDK picks it up by itself.
  2. **Local / BAS (env vars)** — the caller has exported
     `AICORE_CLIENT_ID`, `AICORE_CLIENT_SECRET`, `AICORE_AUTH_URL`,
     `AICORE_BASE_URL` (typically via `.env`).
  3. **Cloud Foundry** — the app is bound to an `aicore` service, so
     credentials live in `VCAP_SERVICES`. We extract them and re-export
     as `AICORE_*` env vars.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


_REQUIRED_ENV_VARS = (
    "AICORE_CLIENT_ID",
    "AICORE_CLIENT_SECRET",
    "AICORE_AUTH_URL",
    "AICORE_BASE_URL",
)


def _has_local_config_file() -> bool:
    return (Path.home() / ".aicore" / "config.json").exists()


def _has_required_env_vars() -> bool:
    return all(os.getenv(var) for var in _REQUIRED_ENV_VARS)


def _apply_vcap() -> bool:
    """Read `aicore` credentials from VCAP_SERVICES and export them. Return True on success."""
    vcap_raw = os.getenv("VCAP_SERVICES")
    if not vcap_raw:
        return False

    vcap = json.loads(vcap_raw)
    instances = vcap.get("aicore") or []
    if not instances:
        return False

    creds = instances[0].get("credentials") or {}
    try:
        os.environ["AICORE_CLIENT_ID"] = creds["clientid"]
        os.environ["AICORE_CLIENT_SECRET"] = creds["clientsecret"]
        os.environ["AICORE_AUTH_URL"] = creds["url"]
        os.environ["AICORE_BASE_URL"] = creds["serviceurls"]["AI_API_URL"]
    except KeyError as e:
        raise RuntimeError(
            f"VCAP_SERVICES.aicore is missing a required field: {e}"
        ) from e

    os.environ.setdefault("AICORE_RESOURCE_GROUP", "default")
    return True


def init_aicore() -> None:
    """Initialise AI Core environment variables. Call once at app start.

    Resolution order: local config file → explicit env vars → VCAP.
    Raises if none of the three scenarios applies.
    """
    if _has_local_config_file():
        logger.info("Using ~/.aicore/config.json for AI Core credentials.")
        return

    if _has_required_env_vars():
        os.environ.setdefault("AICORE_RESOURCE_GROUP", "default")
        logger.info("Using AICORE_* environment variables.")
        return

    if _apply_vcap():
        logger.info("Loaded AI Core credentials from VCAP_SERVICES.")
        return

    raise RuntimeError(
        "AI Core configuration not found. Ensure one of the following:\n"
        "1. Local / BAS: ~/.aicore/config.json exists; OR\n"
        "2. Local / BAS: AICORE_CLIENT_ID / AICORE_CLIENT_SECRET / "
        "AICORE_AUTH_URL / AICORE_BASE_URL env vars are set; OR\n"
        "3. Cloud Foundry: the app is bound to an `aicore` service "
        "(VCAP_SERVICES must contain `aicore`)."
    )
