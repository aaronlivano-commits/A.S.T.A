"""Application configuration loaded from environment / .env file.

NOTE: ``VITE_FIREBASE_*`` values are Vite/frontend env vars (used by the React
client). The backend authenticates via the Firebase **Admin** SDK and only
needs ``FIREBASE_CREDENTIALS_PATH`` / ``FIREBASE_CREDENTIALS_JSON`` /
``FIREBASE_STORAGE_BUCKET`` from the service account.
"""
import os
from functools import lru_cache
from typing import ClassVar, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized settings. Override via environment variables or a `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    app_name: str = "A.S.T.A. Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # --- CORS ---
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    # --- Google Gemini ---
    google_api_key: str = "AQ.Ab8RN6I0vTUrNBKm4VkiXzkwPUZ01TPs0bUg38iTZWT9Iof1pw"
    gemini_text_model: str = "gemini-2.5-flash"
    gemini_vision_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "text-embedding-004"

    # --- Firebase Admin (service-account creds) ---
    # Set ONE of these in your .env file:
    #   FIREBASE_CREDENTIALS_PATH=/abs/path/to/service-account.json
    #   FIREBASE_CREDENTIALS_JSON='{"type":"service_account", ... }'
    firebase_credentials_path: str = ""
    firebase_credentials_json: str = ""
    firebase_storage_bucket: str = ""

    # --- Vector store ---
    vector_store_type: str = "chromadb"  # "chromadb" | "faiss"
    chroma_persist_dir: str = "./.data/chroma"
    vector_store_dir: str = "./.data/vector_stores"
    collection_prefix: str = "asta_topic_"

    # --- RAG ---
    chunk_size: int = 1000
    chunk_overlap: int = 200
    rag_top_k: int = 5
    rag_score_threshold: float = 0.7

    # --- Storage paths (local fallback) ---
    upload_dir: str = "./.data/uploads"
    model_export_dir: str = "./.data/models"
    dataset_dir: str = "./.data/datasets"
    max_upload_size: int = 100 * 1024 * 1024  # 100 MB

    # --- LoRA defaults ---
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = Field(
        default_factory=lambda: ["q_proj", "v_proj"]
    )

    # --- Training defaults ---
    training_batch_size: int = 4
    training_epochs: int = 3
    training_learning_rate: float = 2e-4

    # --- Frontend-only env vars (kept here so a single .env file can drive both
    #     the backend and the Vite client during local development). These are
    #     **not** used by the backend; they are exposed for the frontend to read.
    # Real values come from `frontend/.env`; the backend never reads them.
    VITE_FIREBASE_API_KEY: str = os.environ.get("VITE_FIREBASE_API_KEY", "fallback_key_lokal")
    VITE_FIREBASE_AUTH_DOMAIN: str ="bedrock-8b03e.firebaseapp.com"
    VITE_FIREBASE_PROJECT_ID: str ="bedrock-8b03e"
    VITE_FIREBASE_STORAGE_BUCKET: str ="bedrock-8b03e.firebasestorage.app"
    VITE_FIREBASE_MESSAGING_SENDER_ID: str ="550861317955"
    VITE_FIREBASE_APP_ID: str ="1:550861317955:web:41b11172856704c871b1f6"
    VITE_FIREBASE_MEASUREMENT_ID: str ="G-GF35E62473"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (FastAPI dependency)."""
    return Settings()
