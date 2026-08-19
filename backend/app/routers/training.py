"""Training dataset ingestion (text + vision)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..dependencies import CurrentUser, get_current_user
from ..schemas import TextTrainingResponse, VisionTrainingResponse
from ..services import DatasetTrainer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/training", tags=["training"])

_TEXT_EXT = {".csv", ".json", ".xlsx"}
_VISION_EXT = {".zip"}


@router.post("/text", response_model=TextTrainingResponse, status_code=201)
async def upload_text_dataset(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    filename = (file.filename or "").lower()
    if not any(filename.endswith(ext) for ext in _TEXT_EXT):
        raise HTTPException(
            status_code=415,
            detail="Text training requires .csv, .json, or .xlsx",
        )

    blob = await file.read()
    if not blob:
        raise HTTPException(status_code=400, detail="Empty upload")

    trainer = DatasetTrainer()
    try:
        result = trainer.ingest_text(
            file_bytes=blob, filename=filename, owner_uid=user.uid
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Text dataset ingest failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Ingest failed: {exc}") from exc

    return TextTrainingResponse(
        dataset_id=result.dataset_id,
        rows_ingested=result.rows,
        format=result.format,
        preview=result.preview,
    )


@router.post("/vision", response_model=VisionTrainingResponse, status_code=201)
async def upload_vision_dataset(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
):
    filename = (file.filename or "").lower()
    if not any(filename.endswith(ext) for ext in _VISION_EXT):
        raise HTTPException(status_code=415, detail="Vision training requires a .zip archive")

    blob = await file.read()
    if not blob:
        raise HTTPException(status_code=400, detail="Empty upload")

    trainer = DatasetTrainer()
    try:
        dataset_id, image_count, label_dist, _ = trainer.ingest_vision(
            archive_bytes=blob, filename=filename, owner_uid=user.uid
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Adapter would be produced asynchronously in production; stub for now.
    adapter_id = f"adapter_{dataset_id}"
    trainer.train_lora_adapter(
        dataset_path=str(trainer._base / dataset_id),  # noqa: SLF001
        adapter_id=adapter_id,
    )

    return VisionTrainingResponse(
        dataset_id=dataset_id,
        image_count=image_count,
        label_distribution=label_dist,
        adapter_id=adapter_id,
    )
