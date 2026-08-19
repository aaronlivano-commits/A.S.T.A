"""Pydantic request/response schemas shared across routers."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# --- Auth ---
class AuthVerifyResponse(BaseModel):
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    initialized: bool = True


# --- Topics ---
class TopicBase(BaseModel):
    title: str
    description: Optional[str] = None
    subject: Optional[str] = None


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None


class Topic(TopicBase):
    id: str
    owner_uid: str
    document_count: int = 0
    created_at: datetime
    updated_at: datetime


# --- Documents ---
class DocumentIngestResponse(BaseModel):
    document_id: str
    topic_id: str
    chunks: int
    embeddings_stored: int
    storage_uri: Optional[str] = None


# --- Vision / Lens ---
class VisionAnalyzeRequest(BaseModel):
    topic_id: Optional[str] = None
    prompt: str = "Analyze this region of interest in detail and provide a step-by-step explanation."


class VisionAnalyzeResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    model: str


# --- Chat ---
class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatStreamRequest(BaseModel):
    topic_id: Optional[str] = None
    messages: List[ChatMessage]
    temperature: float = 0.4
    max_tokens: int = 1024


# --- Training ---
class TextTrainingResponse(BaseModel):
    dataset_id: str
    rows_ingested: int
    format: str
    preview: List[dict] = Field(default_factory=list)


class VisionTrainingResponse(BaseModel):
    dataset_id: str
    image_count: int
    label_distribution: dict
    adapter_id: Optional[str] = None


# --- Models / Portability ---
class ModelExportResponse(BaseModel):
    model_id: str
    bundle_uri: str
    size_bytes: int
    includes: List[str]


class ModelImportRequest(BaseModel):
    bundle_uri: Optional[str] = None  # server-side path or cloud storage URI
