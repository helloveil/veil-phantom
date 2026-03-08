"""
VeilPhantom — NLP Entity Detection Layer (Layer 2).
Uses regex-based POS heuristics and pattern matching for entity detection.
No external NLP dependencies required — lightweight alternative to spaCy/NLTK.

Ported from RedactionEngine.swift Layer 2 (NLTagger).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ── POS Rejection Sets ──

# Words that are commonly misclassified as organizations
NOT_ORGS: set[str] = {
    "firm", "firms", "brand", "brands", "management", "company", "companies",
    "venture", "capital", "analytics", "affiliate", "affiliates",
    "redirect", "redirects", "setup", "hosting", "server", "plugin",
    "dashboard", "domain", "caching", "retargeting", "incognito",
    "park", "bridge", "hill", "valley", "meadow", "river", "creek",
    "forest", "lake", "bay", "island", "harbor", "summit", "ridge",
    "spring", "falls", "glen", "grove", "haven", "cove", "cape",
    "tennis", "golf", "yoga", "cricket", "rugby", "soccer", "swimming",
    "running", "hiking", "cycling", "boxing", "surfing", "sailing",
    "coffee", "sage", "cherry", "ginger", "pepper", "olive", "jasmine",
    "violet", "daisy", "ivy", "rose", "lily", "poppy", "willow",
    "sunny", "winter", "dawn", "autumn", "storm", "rain", "frost",
    "pixel", "widget", "buffer", "cache", "stack", "queue", "node",
    "array", "string", "thread", "kernel", "driver", "socket",
    "learning", "training", "testing", "building", "running", "planning",
    "meeting", "working", "talking", "thinking", "looking", "coming",
    "going", "saying", "making", "taking", "giving", "finding",
    "general", "special", "central", "international", "national",
    "global", "local", "regional", "federal", "municipal",
}

# Words commonly misclassified as person names
NOT_NAMES: set[str] = {
    "director", "president", "minister", "secretary", "ambassador",
    "governor", "senator", "congressman", "representative", "judge",
    "justice", "attorney", "prosecutor", "inspector", "commissioner",
    "manager", "executive", "analyst", "engineer", "developer",
    "designer", "architect", "consultant", "advisor", "professor",
    "instructor", "student", "teacher", "lecturer", "researcher",
    "yesterday", "morning", "evening", "afternoon", "tonight",
    "meanwhile", "furthermore", "moreover", "however", "therefore",
    "always", "never", "often", "rarely", "seldom", "sometimes",
    "major", "minor", "senior", "junior", "chief", "lead", "head",
    "first", "second", "third", "last", "next", "final", "previous",
}

# Determiners that can't start an org name
DETERMINERS: set[str] = {
    "these", "those", "some", "many", "the", "a", "an", "all", "any",
    "our", "their", "his", "her", "its",
}

# Generic org phrases (false positives)
GENERIC_ORG_PHRASES: set[str] = {
    "venture capital", "affiliate partners", "affiliate partner",
    "these companies", "those companies", "some companies",
    "the company", "the firm", "the brand",
    "in our capital", "vc venture capital",
}

# NLP stop words — common capitalized words falsely tagged as entities
NLP_STOP_WORDS: set[str] = {
    "His", "Her", "About", "Series", "Board", "Next", "Last",
    "First", "Court", "National", "Global", "South", "North",
    "East", "West", "Center", "Centre", "Learning", "Companies",
    "General", "Special", "Central", "International", "Federal",
    "It's", "Its", "After", "Before", "During", "Between",
    "Always", "Never", "Often", "Rarely", "Seldom", "Sometimes",
    "Meanwhile", "Furthermore", "Moreover", "However", "Therefore",
    "Major", "Minor", "Senior", "Junior", "Chief", "Lead",
    "Yesterday", "Morning", "Evening", "Afternoon", "Tonight",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday", "Sunday", "January", "February", "March", "April",
    "May", "June", "July", "August", "September", "October",
    "November", "December", "Today", "Tomorrow", "Yesterday",
    "I'm", "I'll", "I've", "We're", "They're", "He's", "She's",
    "Going", "Coming", "Looking", "Making", "Taking", "Getting",
    "Running", "Working", "Building", "Testing", "Training",
    "Meeting", "Planning", "Talking", "Thinking", "Finding",
}

# Contraction pattern
_CONTRACTION_RE = re.compile(r"\w+['\u2019][a-z]")

# Speaker diarization tag
_SPEAKER_RE = re.compile(r"^SPEAKER_?S?\d+")

# Capitalized multi-word pattern for entity detection
_CAP_WORD_SEQUENCE_RE = re.compile(r"\b([A-Z][a-zA-Z'-]{2,}(?:\s+[A-Z][a-zA-Z'-]{2,})*)\b")


@dataclass
class NLPEntity:
    """An entity detected by the NLP layer."""
    type: str  # "PERSON" or "ORG"
    value: str


def is_valid_entity(text: str, entity_type: str, context: str) -> bool:
    """Validate a detected entity using POS heuristics.

    Returns False if the entity is likely a false positive.
    Ported from RedactionEngine.swift isValidEntity().
    """
    trimmed = text.strip()

    # Rule 1: Contraction filter
    if _CONTRACTION_RE.search(trimmed):
        return False

    # Rule 2: Speaker diarization tags
    if _SPEAKER_RE.match(trimmed):
        return False

    # Rule 2b: Multi-word ORGs starting with determiner
    if entity_type == "ORG" and " " in trimmed:
        first_word = trimmed.split()[0].lower()
        if first_word in DETERMINERS:
            return False

    # Rule 2c: Generic org phrases
    if entity_type == "ORG" and trimmed.lower() in GENERIC_ORG_PHRASES:
        return False

    # Rule 3a0: Single-word ORG must be at least 4 characters
    if entity_type == "ORG" and " " not in trimmed and len(trimmed) < 4:
        return False

    # Rule 3a: Single lowercase noun as ORG
    if entity_type == "ORG" and " " not in trimmed and trimmed[0:1].islower():
        return False

    # Rule 3b: All-caps short strings as PERSON are acronyms
    if entity_type == "PERSON" and len(trimmed) <= 4 and trimmed == trimmed.upper() and trimmed.isalpha():
        return False

    # Check against stop word lists
    if trimmed in NLP_STOP_WORDS:
        return False
    if entity_type == "ORG" and trimmed.lower() in NOT_ORGS:
        return False
    if entity_type == "PERSON" and trimmed.lower() in NOT_NAMES:
        return False

    # Gerund rejection (-ing words as names)
    if " " not in trimmed and trimmed.endswith("ing") and trimmed[0:1].isupper():
        return False

    return True


def detect_entities(text: str, whitelist: set[str]) -> list[NLPEntity]:
    """Detect PERSON and ORG entities using pattern matching + validation.

    This is a lightweight NLP layer that finds capitalized word sequences
    and validates them against POS heuristics.
    """
    entities: list[NLPEntity] = []
    seen: set[str] = set()

    for m in _CAP_WORD_SEQUENCE_RE.finditer(text):
        value = m.group(1)

        # Skip if in whitelist
        if value.upper() in whitelist:
            continue

        # Skip if already seen
        if value.lower() in seen:
            continue

        # Skip single words that are too common
        words = value.split()
        if len(words) == 1 and len(value) < 3:
            continue

        # Determine type heuristically
        # Multi-word capitalized sequences that contain org keywords → ORG
        org_keywords = {"Inc", "Ltd", "LLC", "Corp", "Group", "Holdings",
                        "Partners", "Ventures", "Capital", "Fund", "Bank",
                        "Trust", "Foundation", "Institute", "University",
                        "Labs", "Studios", "Beauty", "Technologies", "Solutions"}
        is_org = any(w in org_keywords for w in words)

        entity_type = "ORG" if is_org else "PERSON"

        # Validate
        if is_valid_entity(value, entity_type, text):
            entities.append(NLPEntity(type=entity_type, value=value))
            seen.add(value.lower())

    return entities
