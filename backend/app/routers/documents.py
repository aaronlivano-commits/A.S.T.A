"""Document upload + OCR + embedding ingestion."""
from __future__ import annotations

import io
import logging
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..config import get_settings
from ..dependencies import CurrentUser, get_current_user
from ..schemas import DocumentIngestResponse
from ..services import VectorStore, get_gemini_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

_ALLOWED_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/heic",
}


def _chunk_text(
    text: str,
    max_chars: int | None = None,
    overlap: int | None = None,
) -> List[str]:
    """Sliding-window chunker. Sizes come from settings (CHUNK_SIZE / CHUNK_OVERLAP)."""
    settings = get_settings()
    max_chars = max_chars or settings.chunk_size
    overlap = overlap or settings.chunk_overlap
    text = text.strip()
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


@router.post("/upload", response_model=DocumentIngestResponse, status_code=201)
async def upload_document(
    topic_id: str = Form(...),
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=415, detail=f"Unsupported type: {file.content_type}"
        )

    settings = get_settings()
    blob = await file.read()
    if len(blob) > settings.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(blob)} > {settings.max_upload_size} bytes",
        )

    upload_dir = Path(settings.upload_dir) / user.uid / topic_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    doc_id = str(uuid.uuid4())
    stored_path = upload_dir / f"{doc_id}_{file.filename}"
    stored_path.write_bytes(blob)

    # --- OCR / parsing ---
    extracted_text: str = ""
    try:
        if file.content_type == "application/pdf":
            # Real impl: use pdfplumber / pypdf here.
            extracted_text = blob.decode("utf-8", errors="ignore")
        else:
            # Lazy imports so the module loads even if optional CV deps are missing.
            try:
                import easyocr  # type: ignore
                import numpy as np
                from PIL import Image

                reader = easyocr.Reader(["en"], gpu=False, verbose=False)
                img = np.array(Image.open(io.BytesIO(blob)).convert("RGB"))
                result = reader.readtext(img, detail=0, paragraph=True)
                extracted_text = "\n".join(result)
            except Exception as ocr_err:  # noqa: BLE001
                logger.warning("OCR fallback failed (%s) — using empty text", ocr_err)
                extracted_text = ""
    except Exception as exc:  # noqa: BLE001
        logger.exception("Document parse failed: %s", exc)
        raise HTTPException(status_code=422, detail=f"Failed to parse document: {exc}")

    chunks = _chunk_text(extracted_text)
    if not chunks:
        return DocumentIngestResponse(
            document_id=doc_id,
            topic_id=topic_id,
            chunks=0,
            embeddings_stored=0,
            storage_uri=str(stored_path),
        )

    # --- Embed & store ---
    engine = get_gemini_engine()
    embeddings = engine.embed_texts(chunks)
    vs = VectorStore()
    stored = vs.add(
        topic_id,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{"source": file.filename, "document_id": doc_id} for _ in chunks],
        ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
    )

    return DocumentIngestResponse(
        document_id=doc_id,
        topic_id=topic_id,
        chunks=len(chunks),
        embeddings_stored=stored,
        storage_uri=str(stored_path),
    )
