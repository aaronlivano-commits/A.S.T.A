"""Shared FastAPI dependencies (auth guard, current user, etc.)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException, status

from .firebase_config import init_firebase

logger = logging.getLogger(__name__)


@dataclass
class CurrentUser:
    """Authenticated user resolved from a Firebase ID token."""
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    raw_claims: Optional[dict] = None


def _extract_bearer(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return parts[1]


def _try_init_firebase() -> bool:
    """Best-effort Firebase init. Returns True if an admin app is available."""
    try:
        init_firebase()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Firebase Admin unavailable: %s", exc)
        return False


def get_current_user(authorization: Optional[str] = Header(None)) -> CurrentUser:
    """Validate the Firebase ID token and return the resolved user."""
    token = _extract_bearer(authorization)

    if not _try_init_firebase():
        # Frontend gets a clean 401 instead of a 500 while creds are missing.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Server Firebase credentials not configured",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        from firebase_admin import auth as fb_auth  # lazy

        decoded = fb_auth.verify_id_token(token)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return CurrentUser(
        uid=decoded.get("uid", decoded.get("user_id", "")),
        email=decoded.get("email"),
        name=decoded.get("name"),
        picture=decoded.get("picture"),
        raw_claims=decoded,
    )
