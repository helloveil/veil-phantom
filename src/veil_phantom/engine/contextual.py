"""
VeilPhantom — Layer 5: Contextual sensitivity detection.
Detects roles, situations, temporal markers that could identify someone even without names.
"""

from __future__ import annotations

from . import patterns
from .data import PUBLIC_COMPANIES


def has_sensitive_situation(text: str) -> bool:
    return patterns.SENSITIVE_SITUATION.search(text) is not None


def has_sensitive_timing(text: str) -> bool:
    return patterns.TEMPORAL_SENSITIVITY.search(text) is not None


def is_public_company_context(text: str, match_end: int) -> bool:
    """Check if text after a role mention refers to a public company."""
    after = text[match_end:match_end + 50]
    for company in PUBLIC_COMPANIES:
        if company.lower() in after.lower():
            return True
    return False


def is_specific_role_reference(match_text: str) -> bool:
    """Check if the role is a specific reference (e.g. 'the CEO' or 'CEO of')."""
    lower = match_text.lower().strip()
    return lower.startswith("the ") or " of " in lower
