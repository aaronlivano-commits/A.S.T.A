"""Packager for `.asta-model` bundles — zero-retraining sharing.

Bundle layout (zipped):
    manifest.json
    prompt_persona.json
    adapter/                  (LoRA .safetensors + adapter_config.json)
    knowledge/                (vector store dump)
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from ..config import get_settings

logger = logging.getLogger(__name__)


class ModelExporter:
    def __init__(self, export_dir: Optional[str] = None) -> None:
        settings = get_settings()
        self._base = Path(export_dir or settings.model_export_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        *,
        model_id: str,
        owner_uid: str,
        adapter_dir: Optional[str] = None,
        persona: Optional[Dict] = None,
        knowledge_dir: Optional[str] = None,
    ) -> Dict:
        """Build a self-contained .asta-model archive and return its metadata."""
        staging = self._base / f"_stage_{model_id}"
        staging.mkdir(parents=True, exist_ok=True)

        try:
            manifest = {
                "model_id": model_id,
                "owner_uid": owner_uid,
                "version": "1.0",
                "includes": [],
            }

            if adapter_dir and Path(adapter_dir).exists():
                shutil.copytree(adapter_dir, staging / "adapter")
                manifest["includes"].append("adapter")

            if persona:
                (staging / "prompt_persona.json").write_text(
                    json.dumps(persona, indent=2)
                )
                manifest["includes"].append("prompt_persona")

            if knowledge_dir and Path(knowledge_dir).exists():
                shutil.copytree(knowledge_dir, staging / "knowledge")
                manifest["includes"].append("knowledge")

            (staging / "manifest.json").write_text(json.dumps(manifest, indent=2))

            bundle_path = self._base / f"{model_id}.asta-model"
            if bundle_path.exists():
                bundle_path.unlink()

            with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in staging.rglob("*"):
                    if path.is_file():
                        zf.write(path, path.relative_to(staging))

            return {
                "model_id": model_id,
                "bundle_uri": str(bundle_path),
                "size_bytes": bundle_path.stat().st_size,
                "includes": manifest["includes"],
            }
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def import_bundle(self, bundle_path: str, target_owner_uid: str) -> Dict:
        """Decompose a .asta-model bundle and place its parts in the local tree."""
        bundle = Path(bundle_path)
        if not bundle.exists():
            raise FileNotFoundError(bundle_path)

        extract_root = self._base / "imported" / target_owner_uid / bundle.stem
        if extract_root.exists():
            shutil.rmtree(extract_root)
        extract_root.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(bundle) as zf:
            zf.extractall(extract_root)

        manifest = json.loads((extract_root / "manifest.json").read_text())
        return {
            "model_id": manifest.get("model_id"),
            "installed_at": str(extract_root),
            "includes": manifest.get("includes", []),
        }
