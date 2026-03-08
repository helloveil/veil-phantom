"""
VeilPhantom — RedactionResult: the output of redaction with rehydration support.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .types import DetectionSource, SensitiveTokenType, SensitivityLevel

_ORPHAN_TOKEN_RE = re.compile(r"\[[A-Z]+_\d+\]")


@dataclass
class RedactedToken:
    """A single redacted token with metadata."""
    token: str
    type: SensitiveTokenType
    original_value: str
    phantom_value: str | None = None
    sensitivity: SensitivityLevel = SensitivityLevel.MEDIUM
    semantic_score: float | None = None
    source: DetectionSource = DetectionSource.UNKNOWN


@dataclass
class RedactionStats:
    """Statistics about what was redacted."""
    person: int = 0
    org: int = 0
    location: int = 0
    amount: int = 0
    date: int = 0
    phone: int = 0
    email: int = 0
    financial: int = 0
    schedule: int = 0
    credential: int = 0
    gov_id: int = 0
    card: int = 0
    bank_account: int = 0
    ip_address: int = 0
    address: int = 0
    role: int = 0
    situation: int = 0
    temporal: int = 0

    @property
    def total(self) -> int:
        return (self.person + self.org + self.location + self.amount +
                self.date + self.phone + self.email + self.financial +
                self.schedule + self.credential + self.gov_id + self.card +
                self.bank_account + self.ip_address + self.address +
                self.role + self.situation + self.temporal)


@dataclass
class RedactionResult:
    """
    Result of VeilPhantom redaction.

    The primary output is `sanitized` which contains tokens like [PERSON_1], [ORG_1].
    Send `sanitized` directly to your LLM (token-direct mode).
    Then call `rehydrate(ai_response)` to restore original values.
    """
    sanitized: str
    token_map: dict[str, RedactedToken] = field(default_factory=dict)
    stats: RedactionStats = field(default_factory=RedactionStats)

    def rehydrate(self, text: str) -> str:
        """Replace tokens with original values in AI response.

        Also cleans up orphan tokens (AI-hallucinated [ROLE_3] when only ROLE_1, ROLE_2 existed).
        """
        result = text
        # Sort by token length descending to prevent [X_1] matching inside [X_10]
        for token, info in sorted(self.token_map.items(), key=lambda x: len(x[0]), reverse=True):
            result = result.replace(token, info.original_value)
        # Clean up orphan tokens not in our map
        result = _ORPHAN_TOKEN_RE.sub("[redacted]", result)
        return result

    def to_phantom_text(self) -> str:
        """Get phantom-substituted text (legacy mode — realistic fake values)."""
        result = self.sanitized
        for token, info in sorted(self.token_map.items(), key=lambda x: len(x[0]), reverse=True):
            if info.phantom_value:
                result = result.replace(token, info.phantom_value)
        return result

    def reverse_phantom(self, text: str) -> str:
        """Reverse phantom values back to tokens (legacy mode)."""
        result = text
        for token, info in sorted(
            self.token_map.items(),
            key=lambda x: len(x[1].phantom_value or ""),
            reverse=True,
        ):
            if info.phantom_value:
                result = result.replace(info.phantom_value, token)
        return result

    def apply_token_map(self, text: str) -> str:
        """Apply this result's token map to different text (same original values → same tokens)."""
        result = text
        for token, info in sorted(
            self.token_map.items(),
            key=lambda x: len(x[1].original_value),
            reverse=True,
        ):
            result = result.replace(info.original_value, token)
        return result
