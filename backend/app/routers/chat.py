"""RAG-grounded chat streaming endpoint (SSE)."""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..config import get_settings
from ..dependencies import CurrentUser, get_current_user
from ..schemas import ChatStreamRequest
from ..services import VectorStore, get_gemini_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


def _grounding_prompt(topic_id: str | None, history, retrieved: list[dict]) -> str:
    context_block = "\n\n".join(
        f"[Source {i + 1}] {c.get('text', '')}" for i, c in enumerate(retrieved)
    ) or "(no relevant context found)"

    system = (
        "You are A.S.T.A., an AI tutor. Answer the student's question strictly "
        "using the provided study material. If the answer is not present in the "
        "context, say you don't know. Cite sources as [Source N]."
    )

    last_user = next(
        (m["content"] for m in reversed(history) if m["role"] == "user"), ""
    )
    user_prompt = (
        f"Topic: {topic_id or 'general'}\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {last_user}"
    )
    return system, user_prompt


@router.post("/stream")
async def stream_chat(
    payload: ChatStreamRequest,
    user: CurrentUser = Depends(get_current_user),
):
    settings = get_settings()
    engine = get_gemini_engine()
    history = [m.model_dump() for m in payload.messages]

    # --- RAG retrieval ---
    retrieved: list[dict] = []
    if payload.topic_id:
        last_user = next(
            (m["content"] for m in reversed(history) if m["role"] == "user"), ""
        )
        if last_user:
            try:
                q_emb = engine.embed_texts([last_user])[0]
                vs = VectorStore()
                raw = vs.query(
                    payload.topic_id,
                    query_embedding=q_emb,
                    top_k=settings.rag_top_k,
                )
                # Cosine distance: lower is better. 0 == identical, 2 == opposite.
                # Convert score threshold in [0,1] to a max-distance cutoff.
                threshold = settings.rag_score_threshold
                max_distance = max(0.0, min(2.0, 1.0 - threshold))
                filtered = [
                    c for c in raw
                    if c.get("distance") is None or c.get("distance", max_distance) <= max_distance
                ]
                retrieved = filtered or raw[: max(1, settings.rag_top_k // 2)]
            except Exception as exc:  # noqa: BLE001
                logger.warning("RAG retrieval failed: %s", exc)

    system, user_prompt = _grounding_prompt(payload.topic_id, history, retrieved)

    async def event_source() -> AsyncIterator[bytes]:
        # Send the retrieved sources as a first event so the UI can render citations.
        yield f"event: sources\ndata: {json.dumps(retrieved)}\n\n".encode("utf-8")

        try:
            async for token in engine.stream_text(
                [{"role": "user", "content": user_prompt}],
                system_instruction=system,
                temperature=payload.temperature,
                max_tokens=payload.max_tokens,
            ):
                yield f"event: token\ndata: {json.dumps({'text': token})}\n\n".encode("utf-8")
            yield b"event: done\ndata: {}\n\n"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Streaming failed: %s", exc)
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n".encode("utf-8")

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
