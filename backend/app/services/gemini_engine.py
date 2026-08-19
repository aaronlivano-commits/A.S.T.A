"""Google Gemini client wrapper.

Wraps the `google-genai` SDK for text, vision, and streaming generation,
and provides an embedding helper backed by `text-embedding-004`.

The SDK is imported lazily so the rest of the backend can boot even when
the optional dependency is unavailable.
"""
from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Iterable, List, Optional

from ..config import get_settings

logger = logging.getLogger(__name__)


def _import_genai() -> Any:
    """Lazy import of the google-genai SDK."""
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "google-genai is not installed. Run: pip install google-genai"
        ) from exc
    return genai, types


class GeminiEngine:
    """Thin wrapper around the Gemini API used by the routers."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        settings = get_settings()
        key = api_key or settings.google_api_key
        if not key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not configured. Set it in your .env file."
            )
        genai, _ = _import_genai()
        self._client = genai.Client(api_key=key)
        self._text_model = settings.gemini_text_model
        self._vision_model = settings.gemini_vision_model
        self._embedding_model = settings.gemini_embedding_model

    # --- Text ---
    def generate_text(
        self,
        prompt: str,
        *,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> str:
        _, types = _import_genai()
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )
        response = self._client.models.generate_content(
            model=self._text_model,
            contents=prompt,
            config=config,
        )
        return (response.text or "").strip()

    async def stream_text(
        self,
        messages: Iterable[dict],
        *,
        system_instruction: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        _, types = _import_genai()
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )
        # Convert chat-style messages into a single contents list.
        contents: List[types.Content] = []
        for m in messages:
            contents.append(
                types.Content(
                    role=m["role"],
                    parts=[types.Part(text=m["content"])],
                )
            )

        async for chunk in await self._client.aio.models.generate_content_stream(
            model=self._text_model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text

    # --- Vision ---
    def analyze_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        _, types = _import_genai()
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        image_part = types.Part(
            inline_data=types.Blob(mime_type=mime_type, data=image_bytes)
        )
        response = self._client.models.generate_content(
            model=self._vision_model,
            contents=[prompt, image_part],
            config=config,
        )
        return (response.text or "").strip()

    # --- Embeddings ---
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Batch-embed a list of strings using text-embedding-004."""
        if not texts:
            return []
        result = self._client.models.embed_content(
            model=self._embedding_model,
            contents=texts,
        )
        embeddings: List[List[float]] = []
        for emb in result.embeddings or []:
            embeddings.append(list(emb.values))
        return embeddings


_engine_singleton: Optional[GeminiEngine] = None


def get_gemini_engine() -> GeminiEngine:
    """Lazy singleton accessor."""
    global _engine_singleton
    if _engine_singleton is None:
        _engine_singleton = GeminiEngine()
    return _engine_singleton
