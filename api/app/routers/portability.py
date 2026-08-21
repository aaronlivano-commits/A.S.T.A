"""`.asta-model` import/export and `.asta` topic backups."""
from __future__ import annotations

import logging
import os
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..config import get_settings
from ..dependencies import CurrentUser, get_current_user
from ..schemas import ModelExportResponse
from ..services import ModelExporter, VectorStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["portability"])  # paths defined per-route


# --------------------------- Model bundles (.asta-model) ---------------------------
@router.get(
    "/models/export/{model_id}",
    response_model=ModelExportResponse,
)
def export_model(
    model_id: str,
    adapter_dir: Optional[str] = None,
    user: CurrentUser = Depends(get_current_user),
):
    exporter = ModelExporter()
    meta = exporter.export(
        model_id=model_id,
        owner_uid=user.uid,
        adapter_dir=adapter_dir,
        persona={"system": "You are A.S.T.A., a student tutor."},
        # Vector store would be exported from a real install; we pass None for the stub.
        knowledge_dir=None,
    )
    return ModelExportResponse(**meta)


@router.post("/models/import", response_model=dict)
async def import_model(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    if not (file.filename or "").endswith(".asta-model"):
        raise HTTPException(status_code=415, detail="Expected a .asta-model bundle")

    blob = await file.read()
    tmp_dir = Path(get_settings().model_export_dir) / "_incoming" / user.uid
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / file.filename
    tmp_path.write_bytes(blob)

    exporter = ModelExporter()
    try:
        return exporter.import_bundle(str(tmp_path), user.uid)
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


# --------------------------- Topic archives (.asta) ---------------------------
@router.get("/export/{topic_id}")
def export_topic(topic_id: str, user: CurrentUser = Depends(get_current_user)):
    """Bundle a topic's vector store + metadata into a downloadable .asta archive."""
    settings = get_settings()
    out_dir = Path(settings.model_export_dir) / "topics" / user.uid
    out_dir.mkdir(parents=True, exist_ok=True)
    archive_path = out_dir / f"{topic_id}.asta"

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Manifest
        manifest = {
            "topic_id": topic_id,
            "owner_uid": user.uid,
            "version": "1.0",
        }
        zf.writestr("manifest.json", str(manifest).replace("'", '"'))

    if not archive_path.exists():
        raise HTTPException(status_code=500, detail="Failed to build archive")

    return FileResponse(
        path=str(archive_path),
        media_type="application/zip",
        filename=f"{topic_id}.asta",
    )


@router.post("/import")
async def import_topic(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    if not (file.filename or "").endswith(".asta"):
        raise HTTPException(status_code=415, detail="Expected a .asta archive")

    blob = await file.read()
    target_dir = (
        Path(get_settings().model_export_dir) / "topics" / user.uid / "imported"
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file.filename
    target_path.write_bytes(blob)

    return {
        "topic_id": target_path.stem,
        "size_bytes": target_path.stat().st_size,
        "restored_from": str(target_path),
    }
