"""XSUAA JWT validation for the Streamlit backend.

The backend has a public Cloud Foundry route, but it is bound to the same
XSUAA instance as the Approuter. Every incoming request must carry a
valid `Authorization: Bearer <JWT>` header (forwarded by the Approuter
after a successful SSO login). Direct access without a valid token is
rejected, so the public URL is not a backdoor.

Used by `app.py` (Streamlit) to read the JWT from the request headers
(`st.context.headers`) and validate it via SAP's official `sap-xssec`
library.

Behavior summary
----------------
- Cloud Foundry (env=cf): VCAP_SERVICES.xsuaa is present → real validation.
- Local / BAS: no XSUAA binding → validation is bypassed (returns a fake
  "local-dev" identity) so that the existing local workflow still works.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# Public types
# ============================================================
@dataclass
class AuthIdentity:
    """Minimal user identity extracted from a validated JWT."""
    user_name: str
    email: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    is_local_dev: bool = False

    @property
    def display_name(self) -> str:
        if self.given_name and self.family_name:
            return f"{self.given_name} {self.family_name}"
        return self.user_name


# ============================================================
# VCAP / credentials
# ============================================================
def _xsuaa_credentials() -> Optional[dict]:
    """Load XSUAA credentials from VCAP_SERVICES (Cloud Foundry only)."""
    vcap_raw = os.environ.get("VCAP_SERVICES")
    if not vcap_raw:
        return None
    try:
        vcap = json.loads(vcap_raw)
    except json.JSONDecodeError:
        logger.warning("VCAP_SERVICES is not valid JSON; cannot load XSUAA creds.")
        return None
    instances = vcap.get("xsuaa") or []
    if not instances:
        return None
    return instances[0].get("credentials") or None


# ============================================================
# Token validation
# ============================================================
def _strip_bearer(authorization_header: Optional[str]) -> Optional[str]:
    if not authorization_header:
        return None
    parts = authorization_header.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def validate_authorization_header(
    authorization_header: Optional[str],
) -> Optional[AuthIdentity]:
    """Validate the incoming Authorization header.

    Returns:
        - AuthIdentity on success
        - None on failure (token missing/invalid/expired/wrong audience)
    """
    creds = _xsuaa_credentials()

    # ----- Local / BAS: no XSUAA binding → skip validation -----
    if creds is None:
        logger.info(
            "No XSUAA service binding found (local/BAS run). "
            "Skipping JWT validation and using local-dev identity."
        )
        return AuthIdentity(user_name="local-dev", is_local_dev=True)

    # ----- Cloud Foundry: must validate -----
    token = _strip_bearer(authorization_header)
    if not token:
        return None

    try:
        # `sap-xssec` does the heavy lifting:
        # signature (JWKS), issuer, audience, expiration.
        from sap import xssec  # imported lazily so local runs don't need it
    except ImportError as e:
        logger.error("sap-xssec is not installed; cannot validate JWT: %s", e)
        return None

    try:
        ctx = xssec.create_security_context(token, creds)
    except Exception as e:  # noqa: BLE001 — sap-xssec raises various types
        logger.warning("JWT validation failed: %s", e)
        return None

    try:
        user_name = ctx.get_logon_name() or ctx.get_user_name() or "unknown"
    except Exception:  # noqa: BLE001
        user_name = "unknown"

    def _safe(getter):
        try:
            return getter()
        except Exception:  # noqa: BLE001
            return None

    return AuthIdentity(
        user_name=user_name,
        email=_safe(ctx.get_email),
        given_name=_safe(ctx.get_given_name),
        family_name=_safe(ctx.get_family_name),
    )
