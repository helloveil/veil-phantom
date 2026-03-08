"""
VeilPhantom — Auto-download Shade models from HuggingFace Hub.
Supports Shade V7 (default) and V5 (fallback).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("veil_phantom")

SHADE_REPOS = {
    "v7": "karmaUI/shade-v7",
    "v5": "karmaUI/shade-v5",
}

SHADE_MODEL_FILES = {
    "v7": "ShadeV7.onnx",
    "v5": "ShadeV5.onnx",
}

SHADE_FILES = {
    "v7": ["ShadeV7.onnx", "tokenizer.json", "shade_label_map.json", "tokenizer_config.json"],
    "v5": ["ShadeV5.onnx", "tokenizer.json", "shade_label_map.json", "tokenizer_config.json"],
}

CACHE_DIR = Path(os.environ.get("VEIL_CACHE_DIR", Path.home() / ".cache" / "veil"))


def get_model_dir(model_path: str | None = None, version: str = "v7") -> Path:
    """Get or download the Shade model directory.

    Args:
        model_path: Explicit path to model directory. If None, auto-download.
        version: Model version — "v7" (default) or "v5".

    Returns:
        Path to directory containing model files.
    """
    version = version.lower()
    if version not in SHADE_REPOS:
        raise ValueError(f"Unknown Shade version '{version}'. Supported: {list(SHADE_REPOS.keys())}")

    model_filename = SHADE_MODEL_FILES[version]

    if model_path:
        p = Path(model_path)
        if p.is_dir() and (p / model_filename).exists():
            return p
        if p.is_file() and p.name == model_filename:
            return p.parent
        # Also check for the other version's model file in the directory
        for v, fname in SHADE_MODEL_FILES.items():
            if p.is_dir() and (p / fname).exists():
                return p
            if p.is_file() and p.name == fname:
                return p.parent
        raise FileNotFoundError(f"Shade model not found at {model_path}")

    # Check cache
    cached = CACHE_DIR / f"shade-{version}"
    if (cached / model_filename).exists():
        return cached

    # Download from HuggingFace Hub
    return _download_from_hub(cached, version)


def _download_from_hub(target_dir: Path, version: str = "v7") -> Path:
    """Download model files from HuggingFace Hub."""
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        raise ImportError(
            "huggingface-hub is required for auto-download. "
            "Install with: pip install huggingface-hub"
        )

    repo_id = SHADE_REPOS[version]
    files = SHADE_FILES[version]

    target_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading Shade %s model from HuggingFace Hub (%s)...", version.upper(), repo_id)

    for filename in files:
        logger.info("  Downloading %s...", filename)
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            cache_dir=str(CACHE_DIR / "hf_cache"),
            local_dir=str(target_dir),
        )
        logger.info("  ✓ %s", filename)

    logger.info("Shade %s model ready at %s", version.upper(), target_dir)
    return target_dir
