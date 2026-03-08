"""
VeilPhantom — Main client. The primary entry point for PII redaction.
"""

from __future__ import annotations

import logging
from typing import Callable

from .config import VeilConfig
from .engine.pipeline import RedactionPipeline
from .result import RedactionResult
from .shade.downloader import get_model_dir
from .shade.provider import ShadeNERProvider

logger = logging.getLogger("veil_phantom")


class VeilClient:
    """Privacy-preserving PII redaction for AI pipelines.

    Usage::

        from veil_phantom import VeilClient

        veil = VeilClient()
        result = veil.redact("John Smith sent $5M to john@acme.com")
        result.sanitized   # "[PERSON_1] sent [AMOUNT_1] to [EMAIL_1]"
        result.rehydrate(ai_response)  # restore originals
    """

    def __init__(self, config: VeilConfig | None = None):
        self.config = config or VeilConfig()
        self._shade: ShadeNERProvider | None = None
        self._shade_loaded = False

    def _get_shade(self) -> ShadeNERProvider | None:
        """Lazy-load Shade model on first use."""
        if not self.config.enable_shade:
            return None

        if self._shade_loaded:
            return self._shade

        self._shade_loaded = True
        try:
            model_dir = get_model_dir(self.config.shade_model_path)
            self._shade = ShadeNERProvider(
                model_dir=model_dir,
                max_length=self.config.shade_max_length,
            )
            return self._shade
        except Exception as e:
            logger.warning("Shade model not available, using regex-only: %s", e)
            return None

    def redact(self, text: str) -> RedactionResult:
        """Redact PII from text. Returns RedactionResult with tokens.

        Args:
            text: Input text containing potential PII.

        Returns:
            RedactionResult with sanitized text, token map, and stats.
        """
        # Run Shade NER if available
        shade_entities = None
        shade = self._get_shade()
        if shade:
            try:
                raw = shade.predict(text)
                shade_entities = [
                    {"type": e.type, "value": e.value, "confidence": e.confidence}
                    for e in raw
                ]
            except Exception as e:
                logger.warning("Shade inference failed, falling back to regex: %s", e)

        pipeline = RedactionPipeline(self.config)
        return pipeline.redact(text, shade_entities=shade_entities)

    def wrap(
        self,
        text: str,
        llm_fn: Callable[[str], str],
    ) -> str:
        """Redact PII, call LLM with safe text, rehydrate response.

        Args:
            text: Input text with PII.
            llm_fn: Function that takes sanitized text and returns LLM response.

        Returns:
            LLM response with original values restored.
        """
        result = self.redact(text)
        ai_response = llm_fn(result.sanitized)
        return result.rehydrate(ai_response)

    async def awrap(
        self,
        text: str,
        llm_fn: Callable,
    ) -> str:
        """Async version of wrap().

        Args:
            text: Input text with PII.
            llm_fn: Async function that takes sanitized text and returns LLM response.

        Returns:
            LLM response with original values restored.
        """
        result = self.redact(text)
        ai_response = await llm_fn(result.sanitized)
        return result.rehydrate(ai_response)
