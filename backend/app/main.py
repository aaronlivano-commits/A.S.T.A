"""FastAPI entrypoint for the A.S.T.A. backend."""
from __future__ import annotations
import os
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .firebase_config import init_firebase
from .routers import auth, chat, documents, portability, topics, training, vision

import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

if not firebase_admin._apps:
    fb_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if fb_json:
        cred = credentials.Certificate(json.loads(fb_json))
        firebase_admin.initialize_app(cred)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    try:
        init_firebase()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Firebase init skipped/failed: %s", exc)
    yield
    # Shutdown
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Enforce MAX_UPLOAD_SIZE for incoming request bodies.
    @app.middleware("http")
    async def limit_upload_size(request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and cl.isdigit() and int(cl) > settings.max_upload_size:
            return JSONResponse(
                status_code=413,
                content={
                    "detail": (
                        f"Request body too large: {cl} > {settings.max_upload_size}"
                    )
                },
            )
        return await call_next(request)

    prefix = settings.api_v1_prefix
    app.include_router(auth.router, prefix="/api", tags=["auth"])
    app.include_router(topics.router, prefix="/api", tags=["topics"])
    app.include_router(documents.router, prefix="/api", tags=["documents"])
    app.include_router(vision.router, prefix="/api", tags=["vision"])
    app.include_router(chat.router, prefix="/api", tags=["chat"])
    app.include_router(training.router, prefix="/api", tags=["training"])
    app.include_router(portability.router, prefix="/api", tags=["portability"])

    @app.get("/", tags=["health"])
    def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "ok",
        }

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "healthy"}

    return app


app = create_app()

