"""Google Lens-style ROI visual analysis via Gemini Vision."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..dependencies import CurrentUser, get_current_user
from ..schemas import VisionAnalyzeRequest, VisionAnalyzeResponse
from ..services import get_gemini_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vision", tags=["vision"])

_ALLOWED_TYPES = {"image/png", "image/jpeg", "image/webp"}


@router.post("/crop-analyze", response_model=VisionAnalyzeResponse)
async def crop_analyze(
    image: UploadFile = File(...),
    prompt: str = Form(
        "Analyze this region of interest in detail and provide a step-by-step explanation."
    ),
    user: CurrentUser = Depends(get_current_user),
):
    if image.content_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported image type: {image.content_type}")

    blob = await image.read()
    if not blob:
        raise HTTPException(status_code=400, detail="Empty image upload")

    try:
        engine = get_gemini_engine()
        text = engine.analyze_image(
            image_bytes=blob,
            mime_type=image.content_type,
            prompt=prompt,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Vision analysis failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Vision backend error: {exc}")

    return VisionAnalyzeResponse(
        text=text,
        model=engine._vision_model,  # noqa: SLF001
    )


# JSON variant (base64 in payload) for clients that prefer it.
@router.post("/crop-analyze-json", response_model=VisionAnalyzeResponse)
def crop_analyze_json(
    payload: VisionAnalyzeRequest,
    image_b64: str = "",
    user: CurrentUser = Depends(get_current_user),
):
    import base64

    if not image_b64:
        raise HTTPException(status_code=400, detail="image_b64 is required")
    try:
        blob = base64.b64decode(image_b64)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid base64: {exc}")

    engine = get_gemini_engine()
    text = engine.analyze_image(blob, "image/png", payload.prompt)
    return VisionAnalyzeResponse(text=text, model=engine._vision_model)  # noqa: SLF001
