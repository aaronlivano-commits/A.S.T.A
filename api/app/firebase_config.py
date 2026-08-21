"""Firebase Admin SDK initialization.

Loads service-account credentials once and exposes the initialized
`firebase_admin` app plus a Firestore/Storage client accessor.

The `firebase_admin` package is imported lazily so the rest of the app
can boot even if the optional Firebase dependency is not installed
(handy for local development without credentials).
"""
from __future__ import annotations

import os
import firebase_admin
from firebase_admin import credentials

import json
import logging
from pathlib import Path
from typing import Any, Optional

from .config import get_settings

logger = logging.getLogger(__name__)

_initialized_app: Optional[Any] = None
_firebase_module: Optional[Any] = None
_import_error: Optional[BaseException] = None

firebaseConfig = {
  "type": "service_account",
  "project_id": "bedrock-8b03e",
  "private_key_id": "772455d04d4b0b4219336de05cfc28a3058ce726",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCjXyW6Dp+Vcc1H\nvA1e0TSgmb9nCPqMt6WJG5teDCYgWuNp3Fy5Fe3iZ+2tFrTwIra197Rgqg+axqkg\nEH+ejMf1APzHdKlmXdQxPmqc+jgaypmLaC3WRVArsx0A7FkpEP3ByAM5I89PvmpX\nEbBC3eDQylBConeloTNtR5nUqQLezNblklR/K3Ma+4Lf57/AbRRZe6R6HOXIPqKI\nUI1q24coNKrPGhRDnQefcftpgia/7jpvhwV0xy5o87GbFMzxDux8Xqpj43M6pFhI\nAW3CiuEf+ftqwQESna8cU3W40FcABoJQcIi83n8E+BSOaAxYdHVUz6xO8n9Uwwbg\nq2nltI4xAgMBAAECggEAEQyze7zd87M6OLPL82rC4sXY31BlEX1y9aGfb8u1yOej\nVx9rv9clidzNxaQagvskdU4iEXp+AWmdKd7+6pWHoq6VMt2edjPxmqgIaVSFuWoO\nZymaqwN1z/Gz465Gyc3fpbMRfwuZLZnSMD8E1Z2hQjjy8llRQkRWASAZUkPHLGgq\nhAPc1jzpw26HryWn9BMbuCpOEYmCHnFnCDnadIm66Vm2DqFROrqCF+PFuD4/1ucW\ndGUE+lyJClVSlhEF9Jz9ophAgJK6xtftGVm0ulheAHZV29hbQjOddB7XczLzjB04\nhcEmTtpYrIc5nvjEJaIoh8p5zFKltPj3aviveeECYQKBgQDWKOS6AQAtCljepL/H\nI48QuFeWSHAAZqe6PqjxJ0yyPp2tgs7hMdhBaQiYE/KEPkyJz351ZuD+G5D7k1MN\nbg1mHioZiSaVaMQ+wGpUk8Te/x/Cn6lg3ZnvxyBr4dlCRDbm2XuInKjlr52Y8Fkj\nb0HC2BxxZhL/CD6ZwYkQPM4YiQKBgQDDShxOo08ADwPN9V/jI2MVkRUmUsdtg75D\n/Eq9niZBUwsP7NpV7vM/9M1zulKj3erG0lI11akgOy5jLxdeGJOo2y/m98ZEVjza\nPpdNIhTNrVT6onkbf4XnNIy3mvNPYigt7YJLhxkAcCNctj30VKpye/0c5gyVhFsW\n3gpI8e0OaQKBgBUIBw5NMts5fOjAfSTtVQtrTw6vJnCjpC0iIi0skteeVpXHltF+\nt6IU0oc8zkA2bgXKnryg0c+inWZXXXygJii1JaVEVsmtdDhFZSvRJzBPFatjSpr8\nqDVn9MMjdtaPJGUfToZn/B4yVOPEFrzoHCkqWAC66XqqMJug6fjyP7shAoGAGTov\nofDyuZ027pouAteFaznMs6Cp5nnIUFv9A7W0V2f029/K7KLrhW2IRNTi7Aw00e5F\ndHLfYCyE94cTy7H9ESkPbRTA5f8F6WOAhBRM/6zOd3oZjvXQRGfDbcx0deLGMfim\nhj8zeZ0C1G0uX6u4QQXHUr5dDcuFQNT6GyY1a1ECgYAUt6geM2Pn/cpXnjtz12L8\nEUBQCD1daWT1sLvY33zMqhlbGZLslqkMNGvz8EDpSpWnA2R5jB93yjgUiflf1IyC\nbLjxzv7fJChCCij7Fcs0gON23KCaRBcHy6idtHgPoRwABM6Vn3UdPmIriWIrkvaF\nD9gw63Z1ejEGdm0GxjnaZQ==\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@bedrock-8b03e.iam.gserviceaccount.com",
  "client_id": "113059802634720773598",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40bedrock-8b03e.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}


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
    firebase_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if firebase_json:
        try:
            cred_dict = json.loads(firebase_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("INFO: Firebase Admin SDK successfully initialized via JSON String.")
            return
        except Exception as e:
            print(f"ERROR: Failed to parse FIREBASE_CREDENTIALS_JSON: {e}")
            print("WARNING: Firebase Credentials not configured. Backend AI features might throw 500.")
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
