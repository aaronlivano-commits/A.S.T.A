"""Dataset ingestion and lightweight LoRA adapter builder.

Supports:
- Text datasets (CSV / JSON / XLSX) — normalized into QA-pair JSONL
- Vision datasets (ZIP of labeled images) — feeds PEFT/LoRA stub
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from ..config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    dataset_id: str
    rows: int
    format: str
    preview: List[Dict[str, Any]]
    artifact_path: Optional[str] = None


class DatasetTrainer:
    """Parses uploaded training artifacts and prepares them for fine-tuning."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        settings = get_settings()
        self._base = Path(base_dir or settings.dataset_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    # ----- Text -----
    def ingest_text(
        self,
        *,
        file_bytes: bytes,
        filename: str,
        owner_uid: str,
    ) -> IngestResult:
        ext = Path(filename).suffix.lower()
        if ext not in {".csv", ".json", ".xlsx"}:
            raise ValueError(f"Unsupported text dataset format: {ext}")

        df = self._read_tabular(file_bytes, ext)
        df = self._normalize_text_df(df)

        dataset_id = f"text_{owner_uid}_{os.urandom(4).hex()}"
        out_path = self._base / f"{dataset_id}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for _, row in df.iterrows():
                f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

        return IngestResult(
            dataset_id=dataset_id,
            rows=len(df),
            format=ext.lstrip("."),
            preview=df.head(3).to_dict(orient="records"),
            artifact_path=str(out_path),
        )

    @staticmethod
    def _read_tabular(payload: bytes, ext: str) -> pd.DataFrame:
        import io

        if ext == ".csv":
            return pd.read_csv(io.BytesIO(payload))
        if ext == ".json":
            return pd.read_json(io.BytesIO(payload))
        if ext == ".xlsx":
            return pd.read_excel(io.BytesIO(payload))
        raise ValueError(f"Cannot read table format: {ext}")

    @staticmethod
    def _normalize_text_df(df: pd.DataFrame) -> pd.DataFrame:
        """Try to coerce a flexible schema into {instruction, response} pairs."""
        cols = {c.lower().strip(): c for c in df.columns}

        # Already canonical
        if "instruction" in cols and "response" in cols:
            return df[[cols["instruction"], cols["response"]]].rename(
                columns={cols["instruction"]: "instruction", cols["response"]: "response"}
            )

        # Common alternates
        q_aliases = {"question", "q", "prompt", "input", "query"}
        a_aliases = {"answer", "a", "response", "output", "completion", "target"}

        q_col = next((cols[c] for c in q_aliases if c in cols), None)
        a_col = next((cols[c] for c in a_aliases if c in cols), None)

        if q_col and a_col:
            return df[[q_col, a_col]].rename(
                columns={q_col: "instruction", a_col: "response"}
            )

        # Fallback: treat the first two columns as a pair
        if df.shape[1] >= 2:
            return df.iloc[:, :2].rename(
                columns={df.columns[0]: "instruction", df.columns[1]: "response"}
            )

        raise ValueError(
            "Dataset must include at least two columns (e.g. question/answer)."
        )

    # ----- Vision -----
    def ingest_vision(
        self,
        *,
        archive_bytes: bytes,
        filename: str,
        owner_uid: str,
    ) -> Tuple[str, int, Dict[str, int], Optional[str]]:
        if not filename.lower().endswith(".zip"):
            raise ValueError("Vision dataset must be a .zip archive")

        dataset_id = f"vision_{owner_uid}_{os.urandom(4).hex()}"
        extract_dir = self._base / dataset_id
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(io := __import__("io").BytesIO(archive_bytes)) as zf:
            zf.extractall(extract_dir)

        label_dist: Dict[str, int] = {}
        image_count = 0
        for path in extract_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in {
                ".jpg", ".jpeg", ".png", ".bmp", ".webp"
            }:
                image_count += 1
                label = path.parent.name or "unlabeled"
                label_dist[label] = label_dist.get(label, 0) + 1

        # NOTE: actual LoRA fine-tuning would be invoked here via PEFT.
        # For now we return a stub adapter_id pointing at the prepared dataset.
        return dataset_id, image_count, label_dist, str(extract_dir)

    # ----- Adapter training (stub) -----
    def train_lora_adapter(
        self,
        *,
        dataset_path: str,
        adapter_id: str,
    ) -> str:
        """Skeleton that would invoke PEFT/LoRA training.

        Real implementation:
            from peft import LoraConfig, get_peft_model
            ...
        """
        settings = get_settings()
        out_dir = self._base / "adapters" / adapter_id
        out_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "adapter_id": adapter_id,
            "source_dataset": dataset_path,
            "rank": settings.lora_rank,
            "alpha": settings.lora_alpha,
            "dropout": settings.lora_dropout,
            "target_modules": settings.lora_target_modules,
            "training": {
                "batch_size": settings.training_batch_size,
                "epochs": settings.training_epochs,
                "learning_rate": settings.training_learning_rate,
            },
        }
        (out_dir / "adapter_config.json").write_text(json.dumps(meta, indent=2))
        # A safetensors placeholder so the export pipeline has a real file.
        (out_dir / "adapter.safetensors").write_bytes(b"")
        return str(out_dir)
