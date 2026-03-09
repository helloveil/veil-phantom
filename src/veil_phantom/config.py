"""
VeilPhantom — Configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RedactionMode(str, Enum):
    """How to present redacted text to the LLM."""
    TOKEN_DIRECT = "token_direct"   # [PERSON_1], [ORG_1] — default, recommended
    PHANTOM = "phantom"              # Realistic fake values (Alex, TechCorp)
    REDACTED = "redacted"            # [redacted] for everything


@dataclass
class VeilConfig:
    """Configuration for VeilPhantom redaction pipeline."""

    # Layer toggles
    enable_shade: bool = True
    enable_nlp: bool = True
    enable_regex: bool = True
    enable_contextual: bool = True
    enable_gazetteer: bool = True

    # Shade model
    shade_model_path: str | None = None  # None = auto-download from HuggingFace
    shade_max_length: int = 256
    shade_confidence_threshold: float = 0.5
    shade_org_confidence_threshold: float = 0.7

    # Redaction mode
    mode: RedactionMode = RedactionMode.TOKEN_DIRECT

    # Custom data (merged with built-in)
    additional_whitelist: set[str] = field(default_factory=set)
    additional_compound_orgs: set[str] = field(default_factory=set)
    public_companies: list[str] | None = None  # None = use built-in list

    @classmethod
    def regex_only(cls) -> "VeilConfig":
        """Regex + NLP + contextual layers, no Shade model needed.

        The NLP layer is pure Python (no external dependencies) and catches
        person/org names that regex patterns miss.
        """
        return cls(enable_shade=False, enable_nlp=True)

    @classmethod
    def max_privacy(cls) -> "VeilConfig":
        """All layers enabled with aggressive thresholds."""
        return cls(shade_confidence_threshold=0.3, shade_org_confidence_threshold=0.5)
