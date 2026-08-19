"""Firebase Admin SDK initialization.

Loads service-account credentials once and exposes the initialized
`firebase_admin` app plus a Firestore/Storage client accessor.

The `firebase_admin` package is imported lazily so the rest of the app
can boot even if the optional Firebase dependency is not installed
(handy for local development without credentials).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from .config import get_settings

logger = logging.getLogger(__name__)

_initialized_app: Optional[Any] = None
_firebase_module: Optional[Any] = None
_import_error: Optional[BaseException] = None


class FirebaseUnavailable(RuntimeError):
    """Raised when Firebase Admin cannot be imported or initialized.

    Callers (Firestore/Storage accessors, auth dependency) translate this
    into a clean 401/503 instead of a 500.
    """


def _get_firebase():
    """Lazy import of firebase_admin + submodules. Cached after first call."""
    global _firebase_module, _import_error
    if _firebase_module is not None:
        return _firebase_module
    if _import_error is not None:
        raise _import_error
    try:
        import firebase_admin
        from firebase_admin import auth, credentials, firestore, storage

        _firebase_module = {
            "admin": firebase_admin,
            "auth": auth,
            "credentials": credentials,
            "firestore": firestore,
            "storage": storage,
        }
        return _firebase_module
    except Exception as exc:  # noqa: BLE001
        # Some installations have a broken transitive dep (e.g. cryptography
        # DLL mismatch on Windows). Cache the failure so we don't keep
        # crashing on every request.
        logger.warning("firebase_admin import failed: %s", exc)
        _import_error = FirebaseUnavailable(
            f"firebase_admin import failed: {exc}"
        )
        raise _import_error


def _build_credential():
    settings = get_settings()
    try:
        credentials = _get_firebase()["credentials"]
    except FirebaseUnavailable:
        raise

    if settings.firebase_credentials_json:
        logger.info("Initializing Firebase Admin from inline JSON credentials")
        try:
            payload = json.loads(settings.firebase_credentials_json)
        except json.JSONDecodeError as exc:
            raise FirebaseUnavailable(
                "FIREBASE_CREDENTIALS_JSON is set but is not valid JSON. "
                "If you meant to point at a file, use FIREBASE_CREDENTIALS_PATH instead. "
                f"Parse error: {exc}"
            ) from exc
        return credentials.Certificate(payload)

    if settings.firebase_credentials_path:
        path = Path(settings.firebase_credentials_path)
        if not path.is_absolute():
            # Resolve relative paths against the backend root (the directory
            # `uvicorn` was launched from), not the current process CWD which
            # can be misleading when running under `--reload` or tests.
            path = Path.cwd() / path
        if not path.exists():
            raise FirebaseUnavailable(
                f"FIREBASE_CREDENTIALS_PATH points at a missing file: {path}"
            )
        logger.info(
            "Initializing Firebase Admin from credentials file: %s",
            path,
        )
        return credentials.Certificate(str(path))

    raise FirebaseUnavailable(
        "Firebase credentials not configured. Set FIREBASE_CREDENTIALS_PATH "
        "or FIREBASE_CREDENTIALS_JSON in your environment."
    )


def init_firebase() -> Optional[Any]:
    """Initialize the Firebase Admin app exactly once. Safe to call repeatedly.

    Returns the admin app on success, or ``None`` if Firebase cannot be used
    (deps missing, DLL broken, or no service-account configured).
    """
    global _initialized_app
    if _initialized_app is not None:
        return _initialized_app
    try:
        cred = _build_credential()
        fb = _get_firebase()
    except FirebaseUnavailable as exc:
        logger.warning("Firebase init skipped: %s", exc)
        return None
    options: dict = {}
    bucket = get_settings().firebase_storage_bucket
    if bucket:
        options["storageBucket"] = bucket
    _initialized_app = fb["admin"].initialize_app(cred, options or None)
    logger.info("Firebase Admin initialized")
    return _initialized_app


def get_auth():
    if init_firebase() is None:
        raise FirebaseUnavailable("Firebase not available")
    return _get_firebase()["auth"]


def get_firestore():
    if init_firebase() is None:
        raise FirebaseUnavailable("Firebase not available")
    return _get_firebase()["firestore"].client()


def get_storage_bucket():
    if init_firebase() is None:
        raise FirebaseUnavailable("Firebase not available")
    return _get_firebase()["storage"].bucket()
