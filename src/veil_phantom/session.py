"""
VeilPhantom — VeilSession: stateful PII context for multi-turn agent conversations.

Accumulates token_map across turns so tokens stay consistent and new PII
discovered in tool outputs gets properly tracked.

Usage::

    from veil_phantom import VeilSession

    session = VeilSession()
    result = session.redact("Transfer R2.5M from account 62847501234")
    # result.sanitized → "Transfer [AMOUNT_1] from account [BANKACCT_1]"

    # Later, re-redact a tool output that may contain known + new PII
    safe_output = session.redact_tool_output("Transferred R2.5M, ref TXN-99887")
    # → "Transferred [AMOUNT_1], ref TXN-99887"
"""

from __future__ import annotations

import re
from typing import Any

from .client import VeilClient
from .config import VeilConfig
from .result import RedactedToken, RedactionResult

_TOKEN_RE = re.compile(r"\[([A-Z]+)_(\d+)\]")

# Context prefixes that regex patterns capture along with the core value
_CONTEXT_PREFIXES = re.compile(
    r"^(?:account\s*(?:number|no|num)?\.?\s*(?:is|:)?\s*"
    r"|passport\s*(?:number|no|#|num)?\.?\s*(?:is|:)?\s*"
    r"|licen[sc]e\s*(?:number|no|#|num)?\.?\s*(?:is|:)?\s*)",
    re.IGNORECASE,
)


def _extract_core_value(value: str) -> str | None:
    """Extract the core numeric/data part from a context-dependent token value.

    e.g., "account 62847501234" → "62847501234"
    """
    m = _CONTEXT_PREFIXES.match(value)
    if m:
        core = value[m.end():].strip()
        if core:
            return core
    return None


class VeilSession:
    """Stateful session that accumulates PII context across turns."""

    def __init__(self, veil: VeilClient | None = None, config: VeilConfig | None = None):
        if veil is not None:
            self.veil = veil
        else:
            self.veil = VeilClient(config or VeilConfig.regex_only())

        self._token_map: dict[str, RedactedToken] = {}
        self._type_counters: dict[str, int] = {}

    @property
    def token_map(self) -> dict[str, RedactedToken]:
        return self._token_map

    def redact(self, text: str) -> RedactionResult:
        """Redact PII from text and merge new tokens into session state."""
        result = self.veil.redact(text)
        self._merge(result)
        return result

    def rehydrate(self, text: str) -> str:
        """Replace tokens with original values using the cumulative session map."""
        result = text
        for token, info in sorted(self._token_map.items(), key=lambda x: len(x[0]), reverse=True):
            result = result.replace(token, info.original_value)
        return result

    def redact_tool_output(self, text: str) -> str:
        """Re-redact tool output: apply known tokens first, then catch new PII.

        This ensures known PII gets the same tokens, and any new PII
        discovered in the tool output gets fresh tokens that are merged
        into the session.
        """
        # Step 1: Replace known original values with their existing tokens
        # Also try sub-values for context-dependent tokens (e.g., "account 62847501234"
        # should also match bare "62847501234")
        result = text
        for token, info in sorted(
            self._token_map.items(),
            key=lambda x: len(x[1].original_value),
            reverse=True,
        ):
            result = result.replace(info.original_value, token)

        # Step 1b: Try matching the numeric/core part of context-dependent values
        # e.g., "account 62847501234" → try matching bare "62847501234"
        for token, info in self._token_map.items():
            # Extract core value from context-dependent patterns
            core = _extract_core_value(info.original_value)
            if core and core != info.original_value and core in result:
                result = result.replace(core, token)

        # Step 2: Protect existing tokens from being disturbed by re-redaction.
        # Replace them with unique placeholders, re-redact, then restore.
        placeholders: dict[str, str] = {}
        protected = result
        for token in _TOKEN_RE.findall(result):
            full_token = f"[{token[0]}_{token[1]}]"
            if full_token in self._token_map:
                placeholder = f"__VEIL_PROTECTED_{token[0]}_{token[1]}__"
                placeholders[placeholder] = full_token
                protected = protected.replace(full_token, placeholder)

        # Redact any remaining new PII in the unprotected text
        new_result = self.veil.redact(protected)

        if new_result.token_map:
            # Renumber BEFORE restoring placeholders, so renumber only
            # affects new tokens (not the protected existing ones)
            renumbered = self._renumber_result(new_result)
            for placeholder, original_token in placeholders.items():
                renumbered = renumbered.replace(placeholder, original_token)
            return renumbered

        # No new PII found — just restore placeholders
        final = new_result.sanitized
        for placeholder, original_token in placeholders.items():
            final = final.replace(placeholder, original_token)
        return final

    def _merge(self, result: RedactionResult) -> None:
        """Merge a RedactionResult's token_map into session state."""
        for token, info in result.token_map.items():
            if token not in self._token_map:
                self._token_map[token] = info
                # Track the counter
                m = _TOKEN_RE.match(token)
                if m:
                    type_key = m.group(1)
                    num = int(m.group(2))
                    self._type_counters[type_key] = max(
                        self._type_counters.get(type_key, 0), num
                    )

    def _renumber_result(self, result: RedactionResult) -> str:
        """Renumber tokens in a new RedactionResult to avoid session collisions."""
        text = result.sanitized
        remap: dict[str, str] = {}

        for old_token, info in result.token_map.items():
            m = _TOKEN_RE.match(old_token)
            if not m:
                continue

            type_key = m.group(1)

            # Check if this exact original value already has a token in the session
            existing = self._find_token_for_value(info.original_value)
            if existing:
                remap[old_token] = existing
                continue

            # Assign a new counter value
            new_num = self._type_counters.get(type_key, 0) + 1
            self._type_counters[type_key] = new_num
            new_token = f"[{type_key}_{new_num}]"
            remap[old_token] = new_token

            # Merge into session
            new_info = RedactedToken(
                token=new_token,
                type=info.type,
                original_value=info.original_value,
                phantom_value=info.phantom_value,
                sensitivity=info.sensitivity,
                source=info.source,
            )
            self._token_map[new_token] = new_info

        # Apply remap to text (longest first)
        for old, new in sorted(remap.items(), key=lambda x: len(x[0]), reverse=True):
            text = text.replace(old, new)

        return text

    def _find_token_for_value(self, original: str) -> str | None:
        """Find existing session token for an original value."""
        for token, info in self._token_map.items():
            if info.original_value == original:
                return token
        return None
