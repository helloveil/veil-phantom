"""
VeilPhantom — Core redaction pipeline.
Orchestrates all detection layers and produces RedactionResult.
Ported from RedactionEngine.swift.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from ..result import RedactedToken, RedactionResult, RedactionStats
from ..types import DetectionSource, PhantomPools, SensitiveTokenType, SensitivityLevel
from . import contextual, nlp, patterns
from .data import (
    COMMON_FIRST_NAMES,
    COMPOUND_ORGS,
    ORG_CONTEXT_WORDS,
    PUBLIC_COMPANIES,
    TECH_PRODUCTS,
    WHITELIST,
)
from .verbal import verbal_digits_to_numeric, verbal_to_numeric

if TYPE_CHECKING:
    from ..config import VeilConfig

logger = logging.getLogger("veil_phantom")

# Type counter key mapping
_STAT_KEY: dict[SensitiveTokenType, str] = {
    SensitiveTokenType.PERSON: "person",
    SensitiveTokenType.ORG: "org",
    SensitiveTokenType.LOC: "location",
    SensitiveTokenType.AMOUNT: "amount",
    SensitiveTokenType.DATE: "date",
    SensitiveTokenType.PHONE: "phone",
    SensitiveTokenType.EMAIL: "email",
    SensitiveTokenType.FINANCIAL: "financial",
    SensitiveTokenType.SCHEDULE: "schedule",
    SensitiveTokenType.CREDENTIAL: "credential",
    SensitiveTokenType.GOVID: "gov_id",
    SensitiveTokenType.CARD: "card",
    SensitiveTokenType.BANKACCT: "bank_account",
    SensitiveTokenType.IPADDR: "ip_address",
    SensitiveTokenType.ADDRESS: "address",
    SensitiveTokenType.ROLE: "role",
    SensitiveTokenType.SITUATION: "situation",
    SensitiveTokenType.TEMPORAL: "temporal",
}


class RedactionPipeline:
    """Core redaction engine. Detects PII across multiple layers and produces tokens."""

    def __init__(self, config: "VeilConfig"):
        self.config = config
        self._token_counters: dict[SensitiveTokenType, int] = {}
        self._detected_values: set[str] = set()
        self._token_map: dict[str, RedactedToken] = {}
        self._stats = RedactionStats()
        self._text = ""
        self._assigned_phantoms: set[str] = set()

    def redact(
        self,
        text: str,
        shade_entities: list[dict] | None = None,
    ) -> RedactionResult:
        """Run the full redaction pipeline.

        Args:
            text: Input text to redact.
            shade_entities: Optional pre-computed Shade NER results.
                Each dict has keys: type (str), value (str), confidence (float).
        """
        self._text = text
        self._token_counters = {}
        self._detected_values = set()
        self._token_map = {}
        self._stats = RedactionStats()
        self._assigned_phantoms = set()

        # LAYER 0: Shade NER (if provided)
        if shade_entities:
            self._run_shade_layer(shade_entities)

        # LAYER 1: Compound org gazetteer
        if self.config.enable_gazetteer:
            self._run_gazetteer_layer()

        # LAYER 1b: Tech products, contextual ORG, financial institutions
        if self.config.enable_gazetteer:
            self._run_extended_gazetteer_layer()

        # LAYER 1.5: Pre-regex critical patterns (IBAN, spoken email)
        if self.config.enable_regex:
            self._run_pre_regex_layer()

        # LAYER 2: NLP entity detection (POS-validated)
        if self.config.enable_nlp:
            self._run_nlp_layer()

        # LAYER 3: Regex patterns (18 types)
        if self.config.enable_regex:
            self._run_regex_layer()

        # LAYER 3.5: URL/domain detection (skip safe domains)
        if self.config.enable_regex:
            self._run_url_detection()

        # LAYER 5: Contextual sensitivity
        if self.config.enable_contextual:
            self._run_contextual_layer()

        return RedactionResult(
            sanitized=self._text,
            token_map=self._token_map,
            stats=self._stats,
        )

    # ── Layer 0: Shade NER ──

    def _run_shade_layer(self, entities: list[dict]) -> None:
        for ent in entities:
            value = ent.get("value", "").strip()
            ent_type = ent.get("type", "")
            confidence = ent.get("confidence", 0.0)

            # Skip short values, whitelist, underscores, newlines
            if len(value) < 3:
                continue
            if value.startswith("_") or "\n" in value:
                continue
            if value.upper() in WHITELIST:
                continue
            if re.match(r"\[?[A-Z]+_\d+\]?", value):
                continue

            # Skip MONEY — let regex handle (Shade fragments amounts)
            if ent_type == "MONEY":
                continue

            # Map Shade type to our type
            token_type = self._shade_type_to_token_type(ent_type)
            if token_type is None:
                continue

            # ORG confidence threshold
            if token_type == SensitiveTokenType.ORG and confidence < self.config.shade_org_confidence_threshold:
                continue

            # Check if person with org suffix → reclassify as ORG
            if token_type == SensitiveTokenType.PERSON:
                org_suffixes = {"inc", "ltd", "llc", "corp", "corporation", "group",
                                "holdings", "partners", "ventures", "capital", "fund"}
                words = value.lower().split()
                if words and words[-1] in org_suffixes:
                    token_type = SensitiveTokenType.ORG

            self._add_redaction(
                value, token_type,
                sensitivity=SensitivityLevel.HIGH,
                source=DetectionSource.SHADE,
            )

    @staticmethod
    def _shade_type_to_token_type(shade_type: str) -> SensitiveTokenType | None:
        mapping = {
            "PERSON": SensitiveTokenType.PERSON,
            "ORG": SensitiveTokenType.ORG,
            "EMAIL": SensitiveTokenType.EMAIL,
            "PHONE": SensitiveTokenType.PHONE,
            "MONEY": SensitiveTokenType.AMOUNT,
            "DATE": SensitiveTokenType.DATE,
            "ADDRESS": SensitiveTokenType.ADDRESS,
            "GOVID": SensitiveTokenType.GOVID,
            "BANKACCT": SensitiveTokenType.BANKACCT,
            "CARD": SensitiveTokenType.CARD,
            "IPADDR": SensitiveTokenType.IPADDR,
            "CASE": SensitiveTokenType.GOVID,
        }
        return mapping.get(shade_type)

    # ── Layer 1: Compound Org Gazetteer ──

    def _run_gazetteer_layer(self) -> None:
        all_orgs = COMPOUND_ORGS | self.config.additional_compound_orgs
        for org in all_orgs:
            if org.lower() in self._text.lower():
                self._add_redaction(
                    org, SensitiveTokenType.ORG,
                    sensitivity=SensitivityLevel.MEDIUM,
                    source=DetectionSource.GAZETTEER,
                )

    # ── Layer 1b: Extended Gazetteers ──

    def _run_extended_gazetteer_layer(self) -> None:
        text_lower = self._text.lower()

        # Tech products
        for product in TECH_PRODUCTS:
            if product in text_lower:
                # Don't redact tech products — but skip them if NER finds them
                pass

        # Financial institutions
        for m in patterns.FINANCIAL_INSTITUTIONS.finditer(self._text):
            self._add_redaction_exact(
                m.group(), SensitiveTokenType.ORG,
                sensitivity=SensitivityLevel.MEDIUM,
                source=DetectionSource.GAZETTEER,
            )

        # Investment firms
        for m in patterns.INVESTMENT_FIRM.finditer(self._text):
            val = m.group().strip()
            if val.upper() not in WHITELIST and len(val) > 3:
                self._add_redaction_exact(
                    val, SensitiveTokenType.ORG,
                    sensitivity=SensitivityLevel.MEDIUM,
                    source=DetectionSource.GAZETTEER,
                )

        # Contextual ORG detection (capitalized word near org-context words)
        words = self._text.split()
        for i, word in enumerate(words):
            if word[0:1].isupper() and len(word) > 2 and word.upper() not in WHITELIST:
                # Check surrounding words for org context
                context_window = words[max(0, i - 3):i + 4]
                for ctx in context_window:
                    if ctx.lower() in ORG_CONTEXT_WORDS:
                        if word not in COMMON_FIRST_NAMES:
                            self._add_redaction(
                                word, SensitiveTokenType.ORG,
                                sensitivity=SensitivityLevel.MEDIUM,
                                source=DetectionSource.GAZETTEER,
                            )
                        break

    # ── Layer 1.5: Pre-Regex Critical Patterns ──

    def _run_pre_regex_layer(self) -> None:
        # IBAN (must precede other patterns — NLP tags parts like "NWBK" as organizations)
        for m in patterns.IBAN.finditer(self._text):
            self._add_redaction_exact(
                m.group(), SensitiveTokenType.BANKACCT,
                sensitivity=SensitivityLevel.CRITICAL,
                source=DetectionSource.REGEX,
            )

        # Spoken email
        for m in patterns.SPOKEN_EMAIL.finditer(self._text):
            self._add_redaction_exact(
                m.group(), SensitiveTokenType.EMAIL,
                sensitivity=SensitivityLevel.HIGH,
                source=DetectionSource.REGEX,
            )

        # Hybrid email ("sarah at veilprivacy.com")
        for m in patterns.HYBRID_EMAIL.finditer(self._text):
            self._add_redaction_exact(
                m.group(), SensitiveTokenType.EMAIL,
                sensitivity=SensitivityLevel.HIGH,
                source=DetectionSource.REGEX,
            )

    # ── Layer 2: NLP Entity Detection ──

    def _run_nlp_layer(self) -> None:
        whitelist = WHITELIST | {w.upper() for w in (self.config.additional_whitelist or set())}
        entities = nlp.detect_entities(self._text, whitelist)

        for ent in entities:
            token_type = (
                SensitiveTokenType.PERSON if ent.type == "PERSON"
                else SensitiveTokenType.ORG
            )
            # Don't redact if it's a common first name tagged as ORG
            if token_type == SensitiveTokenType.ORG and ent.value in COMMON_FIRST_NAMES:
                continue
            self._add_redaction(
                ent.value, token_type,
                sensitivity=SensitivityLevel.MEDIUM,
                source=DetectionSource.UNKNOWN,  # NLP source
            )

    # ── Layer 3.5: URL/Domain Detection ──

    def _run_url_detection(self) -> None:
        for m in patterns.URL_DOMAIN.finditer(self._text):
            url = m.group()
            # Extract domain
            domain = (
                url.replace("https://", "")
                .replace("http://", "")
                .replace("www.", "")
                .lower()
                .split("/")[0]
            )
            if domain not in patterns.SAFE_DOMAINS:
                self._add_redaction_exact(
                    url, SensitiveTokenType.ADDRESS,
                    sensitivity=SensitivityLevel.MEDIUM,
                    source=DetectionSource.REGEX,
                )

    # ── Layer 3: Regex Patterns ──

    def _run_regex_layer(self) -> None:
        # Order matters! SA ID must run before phone patterns.
        regex_rules: list[tuple[re.Pattern, SensitiveTokenType, SensitivityLevel, bool]] = [
            # Money
            (patterns.USD, SensitiveTokenType.AMOUNT, SensitivityLevel.HIGH, False),
            (patterns.RAND_PREFIX, SensitiveTokenType.AMOUNT, SensitivityLevel.HIGH, False),
            (patterns.RAND_SUFFIX, SensitiveTokenType.AMOUNT, SensitivityLevel.HIGH, False),
            (patterns.VERBAL_AMOUNT, SensitiveTokenType.AMOUNT, SensitivityLevel.HIGH, False),
            (patterns.BARE_NUMERIC_AMOUNT, SensitiveTokenType.AMOUNT, SensitivityLevel.HIGH, False),
            # Email
            (patterns.EMAIL, SensitiveTokenType.EMAIL, SensitivityLevel.HIGH, False),
            # Phone
            (patterns.PHONE_INTL, SensitiveTokenType.PHONE, SensitivityLevel.HIGH, False),
            (patterns.PHONE_US, SensitiveTokenType.PHONE, SensitivityLevel.HIGH, False),
            (patterns.PHONE_SA, SensitiveTokenType.PHONE, SensitivityLevel.HIGH, False),
            (patterns.PHONE_LOCAL, SensitiveTokenType.PHONE, SensitivityLevel.HIGH, False),
            (patterns.SPOKEN_PHONE, SensitiveTokenType.PHONE, SensitivityLevel.HIGH, False),
            # Spoken forms (context regex — use group 0)
            (patterns.SPOKEN_BANK_ACCOUNT, SensitiveTokenType.BANKACCT, SensitivityLevel.CRITICAL, False),
            (patterns.SPOKEN_GOV_ID, SensitiveTokenType.GOVID, SensitivityLevel.CRITICAL, False),
            # Gov IDs (BEFORE dates to prevent SSN→DATE misclassification)
            (patterns.SSN, SensitiveTokenType.GOVID, SensitivityLevel.CRITICAL, False),
            (patterns.SA_ID, SensitiveTokenType.GOVID, SensitivityLevel.CRITICAL, False),
            # Dates
            (patterns.DATE_MONTH, SensitiveTokenType.DATE, SensitivityLevel.LOW, False),
            (patterns.DATE_NUMERIC, SensitiveTokenType.DATE, SensitivityLevel.LOW, False),
            (patterns.DATE_RELATIVE, SensitiveTokenType.DATE, SensitivityLevel.LOW, False),
            (patterns.SPOKEN_DATE, SensitiveTokenType.DATE, SensitivityLevel.LOW, False),
            # Financial instruments
            (patterns.CREDIT_CARD, SensitiveTokenType.CARD, SensitivityLevel.CRITICAL, False),
            # Network/Address
            (patterns.IPV4, SensitiveTokenType.IPADDR, SensitivityLevel.MEDIUM, False),
            (patterns.STREET_ADDRESS, SensitiveTokenType.ADDRESS, SensitivityLevel.HIGH, False),
            # Context-dependent (use capture group 1 if present)
            (patterns.PASSPORT, SensitiveTokenType.GOVID, SensitivityLevel.CRITICAL, True),
            (patterns.DRIVERS_LICENSE, SensitiveTokenType.GOVID, SensitivityLevel.CRITICAL, True),
            (patterns.BANK_ACCOUNT, SensitiveTokenType.BANKACCT, SensitivityLevel.CRITICAL, True),
        ]

        for pattern, token_type, sensitivity, use_group1 in regex_rules:
            for m in pattern.finditer(self._text):
                if use_group1 and m.lastindex and m.lastindex >= 1:
                    value = m.group(1)
                else:
                    value = m.group(0)

                value = value.strip()
                if not value:
                    continue

                # Verbal amount normalization
                if token_type == SensitiveTokenType.AMOUNT and pattern in (patterns.VERBAL_AMOUNT,):
                    normalized = verbal_to_numeric(value)
                    self._add_redaction_exact(
                        m.group(0), token_type,
                        sensitivity=sensitivity,
                        source=DetectionSource.REGEX,
                        display_value=normalized,
                    )
                    continue

                # Spoken digit normalization
                if token_type in (SensitiveTokenType.PHONE, SensitiveTokenType.BANKACCT, SensitiveTokenType.GOVID):
                    if pattern in (patterns.SPOKEN_PHONE, patterns.SPOKEN_BANK_ACCOUNT, patterns.SPOKEN_GOV_ID):
                        self._add_redaction_exact(
                            m.group(0), token_type,
                            sensitivity=sensitivity,
                            source=DetectionSource.REGEX,
                        )
                        continue

                if use_group1:
                    # For context-dependent patterns, redact the full match
                    self._add_redaction_exact(
                        m.group(0), token_type,
                        sensitivity=sensitivity,
                        source=DetectionSource.REGEX,
                    )
                else:
                    self._add_redaction_exact(
                        value, token_type,
                        sensitivity=sensitivity,
                        source=DetectionSource.REGEX,
                    )

    # ── Layer 5: Contextual Sensitivity ──

    def _run_contextual_layer(self) -> None:
        text = self._text
        has_situation = contextual.has_sensitive_situation(text)
        has_timing = contextual.has_sensitive_timing(text)

        # 5a: Identifying roles
        for m in patterns.IDENTIFYING_ROLE.finditer(text):
            match_text = m.group()
            # Skip if followed by public company
            if contextual.is_public_company_context(text, m.end()):
                continue
            # Only redact if sensitive context or specific reference
            if has_situation or has_timing or contextual.is_specific_role_reference(match_text):
                self._add_redaction_exact(
                    match_text, SensitiveTokenType.ROLE,
                    sensitivity=SensitivityLevel.HIGH,
                    source=DetectionSource.CONTEXTUAL,
                )

        # 5b: Sensitive situations
        for m in patterns.SENSITIVE_SITUATION.finditer(text):
            self._add_redaction_exact(
                m.group(), SensitiveTokenType.SITUATION,
                sensitivity=SensitivityLevel.HIGH,
                source=DetectionSource.CONTEXTUAL,
            )

        # 5c: Temporal sensitivity
        for m in patterns.TEMPORAL_SENSITIVITY.finditer(text):
            self._add_redaction_exact(
                m.group(), SensitiveTokenType.TEMPORAL,
                sensitivity=SensitivityLevel.HIGH,
                source=DetectionSource.CONTEXTUAL,
            )

        # 5d: Unique descriptors
        for m in patterns.UNIQUE_DESCRIPTOR.finditer(text):
            self._add_redaction_exact(
                m.group(), SensitiveTokenType.SITUATION,
                sensitivity=SensitivityLevel.HIGH,
                source=DetectionSource.CONTEXTUAL,
            )

    # ── Helpers ──

    def _next_token(self, token_type: SensitiveTokenType) -> str:
        count = self._token_counters.get(token_type, 0) + 1
        self._token_counters[token_type] = count
        return f"[{token_type.value}_{count}]"

    def _get_phantom(self, token_type: SensitiveTokenType, original: str) -> str | None:
        pool = PhantomPools.get_pool(token_type)
        for phantom in pool:
            if phantom != original and phantom not in self._assigned_phantoms:
                self._assigned_phantoms.add(phantom)
                return phantom
        # Fallback: use first pool value
        return pool[0] if pool else None

    def _is_already_detected(self, value: str) -> bool:
        clean = re.sub(r"[.,;:!?]+$", "", value)
        return clean.lower() in self._detected_values

    def _mark_detected(self, value: str) -> None:
        clean = re.sub(r"[.,;:!?]+$", "", value)
        self._detected_values.add(clean.lower())

    def _add_redaction(
        self,
        original: str,
        token_type: SensitiveTokenType,
        sensitivity: SensitivityLevel = SensitivityLevel.MEDIUM,
        source: DetectionSource = DetectionSource.UNKNOWN,
    ) -> None:
        """Add redaction using word-boundary replacement."""
        if not original or len(original) < 2:
            return
        if original.upper() in WHITELIST or original.upper() in (self.config.additional_whitelist or set()):
            return
        if self._is_already_detected(original):
            return

        # Word-boundary replacement
        escaped = re.escape(original)
        pat = re.compile(r"\b" + escaped + r"\b")
        if not pat.search(self._text):
            return

        token = self._next_token(token_type)
        phantom = self._get_phantom(token_type, original)

        self._token_map[token] = RedactedToken(
            token=token,
            type=token_type,
            original_value=original,
            phantom_value=phantom,
            sensitivity=sensitivity,
            source=source,
        )

        self._text = pat.sub(token, self._text)
        self._mark_detected(original)
        self._increment_stat(token_type)

    def _add_redaction_exact(
        self,
        original: str,
        token_type: SensitiveTokenType,
        sensitivity: SensitivityLevel = SensitivityLevel.MEDIUM,
        source: DetectionSource = DetectionSource.UNKNOWN,
        display_value: str | None = None,
    ) -> None:
        """Add redaction using exact string replacement."""
        if not original or len(original) < 2:
            return
        if self._is_already_detected(original):
            return
        if original not in self._text:
            return

        token = self._next_token(token_type)
        phantom = self._get_phantom(token_type, display_value or original)

        self._token_map[token] = RedactedToken(
            token=token,
            type=token_type,
            original_value=original,
            phantom_value=phantom,
            sensitivity=sensitivity,
            source=source,
        )

        self._text = self._text.replace(original, token, 1)
        self._mark_detected(original)
        self._increment_stat(token_type)

    def _increment_stat(self, token_type: SensitiveTokenType) -> None:
        key = _STAT_KEY.get(token_type)
        if key:
            setattr(self._stats, key, getattr(self._stats, key) + 1)
