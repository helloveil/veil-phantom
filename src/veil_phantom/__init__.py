"""
VeilPhantom — Privacy-preserving PII redaction for AI pipelines.

Usage::

    from veil_phantom import VeilClient

    veil = VeilClient()
    result = veil.redact("John Smith sent $5M to john@acme.com")

    # Send sanitized text to your LLM (token-direct mode)
    ai_response = your_llm(result.sanitized)

    # Restore original values
    final = result.rehydrate(ai_response)
"""

from .client import VeilClient
from .config import RedactionMode, VeilConfig
from .result import RedactedToken, RedactionResult, RedactionStats
from .types import DetectionSource, PhantomPools, SensitiveTokenType, SensitivityLevel

__version__ = "1.0.0"
__all__ = [
    "VeilClient",
    "VeilConfig",
    "RedactionMode",
    "RedactionResult",
    "RedactedToken",
    "RedactionStats",
    "SensitiveTokenType",
    "SensitivityLevel",
    "DetectionSource",
    "PhantomPools",
]
