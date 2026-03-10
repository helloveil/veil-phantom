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
# Ported from RedactionEngine.swift isValidEntity() Rule 3b1b
NOT_ORGS: set[str] = {
    # Department / function names
    "leadership", "management", "engineering", "marketing",
    "operations", "communications", "analytics", "accounting",
    "procurement", "logistics", "compliance", "governance",
    "administration", "sales", "finance", "treasury",
    "legal", "audit", "security", "support", "research",
    "development", "design", "strategy", "planning",
    "recruitment", "onboarding", "payroll", "benefits",
    "training", "quality", "assurance", "infrastructure",
    # Abstract nouns / qualities
    "qualities", "innovation", "excellence", "integrity",
    "sustainability", "accountability", "transparency",
    "efficiency", "productivity", "profitability",
    "competitiveness", "reliability", "scalability",
    "flexibility", "diversity", "inclusion", "equity",
    "collaboration", "partnership", "mentorship",
    "stewardship", "ownership", "citizenship",
    # Meeting / business words
    "agenda", "minutes", "budget", "forecast", "pipeline",
    "roadmap", "milestone", "deliverable", "timeline",
    "deadline", "objective", "initiative", "priority",
    "stakeholder", "benchmark", "metric", "quarterly",
    "annual", "revenue", "margin", "overhead", "allocation",
    "restructuring", "downsizing", "outsourcing",
    # Activities / concepts
    "networking", "brainstorming", "onboarding", "offboarding",
    "mentoring", "coaching", "consulting", "freelancing",
    "volunteering", "fundraising", "campaigning",
    "advertising", "branding", "positioning", "segmentation",
    "automation", "digitization", "optimization",
    "consolidation", "integration", "migration",
    "implementation", "deployment", "maintenance",
    "monitoring", "reporting", "documentation",
    # Generic capitalized words misread as ORG
    "premium", "enterprise", "professional", "advanced",
    "standard", "basic", "essential", "ultimate", "express",
    "signature", "platinum", "diamond", "infinity",
    "nationwide", "worldwide", "continental", "regional",
    "downtown", "midtown", "uptown", "suburban", "rural",
    "wholesale", "retail", "commercial", "residential",
    "industrial", "municipal", "federal", "provincial",
    # Original SDK set
    "firm", "firms", "brand", "brands", "company", "companies",
    "venture", "capital", "affiliate", "affiliates",
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
    "learning", "testing", "building", "planning",
    "meeting", "working", "talking", "thinking", "looking", "coming",
    "going", "saying", "making", "taking", "giving", "finding",
    "general", "special", "central", "international", "national",
    "global", "local", "regional",
}

# Words commonly misclassified as person names
# Ported from RedactionEngine.swift isValidEntity() Rule 3b2
NOT_NAMES: set[str] = {
    # Tech / business nouns
    "hosting", "server", "plugin", "meeting", "billing",
    "manager", "admin", "editor", "builder", "loading",
    "pricing", "setting", "update", "storage", "running",
    "testing", "tracking", "mapping", "reading", "writing",
    "speed", "cloud", "mother", "desk", "wireless",
    "clicks", "clients", "eats", "flow",
    "console", "canvas", "academy", "search", "maps", "vibe",
    "parking", "pilates", "managing", "leads",
    "qualities", "leadership",

    # Job titles / roles (capitalized at sentence start)
    "director", "president", "chairman", "chairwoman",
    "chancellor", "governor", "mayor", "senator",
    "congressman", "representative", "ambassador",
    "commissioner", "superintendent", "sergeant",
    "lieutenant", "captain", "colonel", "general",
    "admiral", "commander", "inspector", "detective",
    "officer", "deputy", "minister", "secretary",
    "treasurer", "comptroller", "auditor", "registrar",
    "provost", "dean", "principal", "headmaster",
    "professor", "lecturer", "instructor", "tutor",
    "analyst", "architect", "consultant", "specialist",
    "coordinator", "supervisor", "foreman", "technician",
    "therapist", "counselor", "physician", "surgeon",
    "dentist", "pharmacist", "nurse", "paramedic",
    "attorney", "solicitor", "barrister", "advocate",
    "accountant", "actuary", "broker", "underwriter",
    "recruiter", "interviewer", "moderator", "facilitator",
    "custodian", "warden", "steward", "trustee",
    "executive", "engineer", "developer",
    "designer", "advisor", "researcher",
    "student", "teacher", "judge", "justice",
    "prosecutor",

    # Sports / activities / hobbies
    "yoga", "tennis", "golf", "swimming",
    "cricket", "rugby", "soccer", "football", "baseball",
    "basketball", "volleyball", "hockey", "lacrosse",
    "boxing", "wrestling", "fencing", "archery",
    "cycling", "rowing", "sailing", "surfing",
    "skiing", "snowboarding", "climbing", "hiking",
    "jogging", "marathon", "triathlon", "gymnastics",
    "karate", "judo", "taekwondo", "kickboxing",
    "dance", "ballet", "salsa", "zumba",
    "chess", "poker", "bingo", "bowling",
    "meditation", "fitness", "crossfit", "aerobics",

    # Common nouns often capitalized (sentence start)
    "park", "hill", "bridge", "valley", "ridge",
    "lake", "river", "creek", "grove", "meadow",
    "forest", "woods", "field", "garden", "ranch",
    "harbor", "bay", "beach", "island", "summit",
    "tower", "castle", "manor", "lodge", "villa",
    "chapel", "temple", "cathedral", "mosque",
    "stadium", "arena", "plaza", "terrace", "court",
    "station", "terminal", "depot", "pier", "dock",
    "market", "mall", "center", "centre", "complex",
    "clinic", "hospital", "pharmacy", "lab",

    # Common words / nouns that are also surnames
    "young", "long", "black", "white", "green", "brown",
    "gray", "grey", "noble", "rich", "wise", "strong",
    "sharp", "swift", "stern", "cross", "best", "price",
    "cash", "bond", "dale", "lane", "stone",
    "banks", "wells", "fields", "marsh",
    "bush", "stock", "sterling",

    # Abstract / common nouns
    "agenda", "budget", "review", "status", "report",
    "summary", "overview", "draft", "version", "release",
    "launch", "target", "scope", "phase", "stage",
    "chapter", "section", "segment", "module", "unit",
    "model", "template", "pattern", "format", "layout",
    "bonus", "premium", "discount", "margin", "surplus",
    "deficit", "balance", "volume", "capacity", "quota",
    "threshold", "benchmark", "baseline", "ceiling",
    "average", "median", "total", "maximum", "minimum",

    # Common verbs / adjectives misread as names
    "major", "minor", "senior", "junior", "prime",
    "chief", "master", "champion", "pioneer", "veteran",
    "supreme", "sovereign", "royal", "imperial",
    "cardinal", "premier", "elite",
    "divine", "haven", "grace", "hope", "faith",
    "joy", "chance", "fortune", "sage",

    # Food / drink / household
    "coffee", "latte", "espresso", "mocha", "chai",
    "ginger", "basil", "rosemary", "olive",
    "cherry", "berry", "peach", "plum", "hazel",
    "pepper", "candy", "cookie", "brownie", "biscuit",

    # Weather / nature / time
    "sunny", "stormy", "cloudy", "rainy", "windy",
    "winter", "summer", "spring", "autumn", "dawn",
    "dusk", "midnight", "noon", "sunrise", "sunset",
    "yesterday", "morning", "evening", "afternoon", "tonight",

    # Tech / generic
    "pixel", "widget", "avatar", "cursor", "buffer",
    "cache", "proxy", "socket", "router", "modem",
    "scanner", "printer", "sensor", "beacon", "drone",

    # Original SDK set additions
    "meanwhile", "furthermore", "moreover", "however", "therefore",
    "always", "never", "often", "rarely", "seldom", "sometimes",
    "first", "second", "third", "last", "next", "final", "previous",
    "head", "lead",
    "contact", "please", "dear", "hello", "welcome",
    "met", "called", "sent", "asked", "told", "said", "got", "had",
    "saw", "did", "ran", "let", "set", "put", "cut", "hit", "won",
    "ate", "sat", "led", "paid", "kept", "left", "held", "brought",
    "thought", "found", "gave", "took", "made", "went", "came",
    "based", "given", "noted", "discussed", "reviewed", "confirmed",
    "scheduled", "processed", "completed", "submitted", "approved",
    "contacted", "transferred", "reported", "flagged", "raised",
    "transfer", "process", "prepare", "draft", "create", "update",
    "submit", "check", "verify", "assign", "forward",
    "attach", "include", "summarize", "schedule", "arrange",
    "acquisition", "merger", "proposal", "agreement", "contract",
    "offer", "deal", "transaction", "payment", "invoice", "receipt",
    "follow", "response", "reply", "confirmation", "notification",
    "regarding", "concerning", "about", "subject",
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

# NLP stop words — common capitalized words falsely tagged as entities.
# These are checked case-sensitively (capitalized form = sentence-start false positive).
# Ported from RedactionPatterns.swift nlpStopWords (318 entries).
NLP_STOP_WORDS: set[str] = {
    # Pronouns / contractions
    "His", "Her", "He's", "She's", "It's", "Its",
    "I'm", "I'll", "I've", "We're", "They're",
    "Ourselves", "Themselves", "Yourself", "Itself", "Himself", "Herself",
    # Prepositions / conjunctions
    "About", "After", "Before", "During", "Between", "Within", "Without",
    "Above", "Below", "Inside", "Outside", "Around", "Along",
    "Beyond", "Toward", "Against", "Across", "Behind", "Beside",
    "Here", "There", "Where", "When", "While", "Since", "Until",
    # Adverbs / conjunctive adverbs
    "Meanwhile", "Furthermore", "Moreover", "Nevertheless",
    "Nonetheless", "Therefore", "Otherwise", "Regardless",
    "Certainly", "Obviously", "Apparently", "Presumably",
    "Perhaps", "Maybe", "Likely", "Unlikely", "Possibly",
    "Sometimes", "Always", "Never", "Often", "Rarely", "Seldom",
    "Usually", "Typically", "Normally", "Generally", "Basically",
    "Actually", "Honestly", "Seriously", "Literally", "Absolutely",
    "Exactly", "Simply", "Really", "Truly", "Merely", "Hardly",
    "Certainly", "Definitely", "Undoubtedly", "Clearly",
    # Determiners / quantifiers
    "Both", "Either", "Neither", "Each", "Every", "Some", "Many",
    "Most", "Several", "Few", "All", "Any", "Such", "Other",
    "Another", "Certain", "Various", "Numerous", "Entire",
    "Whole", "Similar", "Different", "Specific", "Particular",
    # Adjectives commonly sentence-initial
    "Major", "Minor", "Primary", "Secondary", "Additional",
    "Essential", "Critical", "Important", "Significant",
    "Relevant", "Appropriate", "Necessary", "Required",
    "Available", "Possible", "Potential", "Effective",
    "Successful", "Professional", "Technical", "Financial",
    "Annual", "Quarterly", "Monthly", "Weekly", "Daily",
    "Internal", "External", "Overall", "Total", "Final",
    "Initial", "Preliminary", "Interim", "Ongoing", "Upcoming",
    "Previous", "Existing", "Proposed", "Expected", "Estimated",
    "Approximate", "Average", "Maximum", "Minimum",
    # Participial adjectives / gerunds
    "Following", "Regarding", "According", "Including",
    "Excluding", "Concerning", "Considering", "Assuming",
    "Depending", "Compared", "Provided", "Supposed",
    "Going", "Coming", "Looking", "Making", "Taking", "Getting",
    "Running", "Working", "Building", "Testing", "Training",
    "Meeting", "Planning", "Talking", "Thinking", "Finding",
    # Time / calendar
    "Today", "Tomorrow", "Yesterday", "Morning", "Evening",
    "Afternoon", "Overnight", "Weekend", "Weekday",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday", "Sunday", "January", "February", "March", "April",
    "May", "June", "July", "August", "September", "October",
    "November", "December",
    # Directions / geographic
    "National", "Global", "South", "North", "East", "West",
    "Central", "International", "Local",
    "General", "Special",
    # Nouns commonly capitalized in headings
    "Series", "Board", "Next", "Last", "First",
    "Court", "Center", "Centre", "Learning", "Companies",
    "Accounts", "Partners", "Affiliate", "These", "Those",
    # Connectors / discourse markers
    "Because", "However", "Although", "Whether", "Through",
    "Online", "Digital", "Standard", "Current", "Recent",
    # Filler words / interjections (common in transcripts)
    "Like", "Just", "Only", "Even", "Still", "Already", "Also",
    "Again", "Indeed", "Instead", "Anyway",
    "Everything", "Something", "Nothing", "Anything",
    "Everyone", "Someone", "Anyone", "Nobody", "Somebody",
    # Common verbs capitalized at sentence start
    "Let", "Got", "Did", "Does", "Has", "Had", "Was", "Were",
    "Can", "Could", "Should", "Would", "Will", "Shall", "Must",
    "Need", "Want", "Know", "Think", "See", "Look", "Feel",
    "Give", "Take", "Make", "Come", "Keep", "Put", "Say",
    "Tell", "Ask", "Try", "Use", "Find", "Get", "Set",
    # Common sentence-start words in conversational transcripts
    "Yeah", "Yep", "Nah", "Nope", "Sure", "Okay", "Alright",
    "Well", "Right", "Cool", "Great", "Nice", "Good", "Fine",
    "Thanks", "Thank", "Sorry", "Please", "Hello", "Hey", "Bye",
    "Wow", "Hmm", "Ugh", "Huh", "Mhm", "Uhm", "Umm", "Mm-hmm", "Uh-huh",
    "Appreciate", "Understood", "Confirmed", "Agreed",
    # Common nouns/adjectives that aren't entities
    "Okay", "Perfect", "Correct", "Exactly", "True", "False",
    "Yes", "No", "Not", "But", "And", "For", "Nor", "Yet", "So",
    "Are", "Were", "Been", "Being", "Have", "Having",
    "Do", "Does", "Doing", "Done",
    "One", "Two", "Three", "Four", "Five", "Six", "Seven",
    "Eight", "Nine", "Ten", "Hundred", "Thousand", "Million",
    # Pronouns (capitalized at sentence start)
    "She", "Him", "They", "Them", "We", "Us",
    "Mine", "Yours", "Ours", "Theirs",
    "This", "That", "What", "Which", "Who", "Whom",
}

# Common English words (lowercase) that should never be entities.
# This catches sentence-initial capitalized common words that slip through
# the capitalized NLP_STOP_WORDS check.
COMMON_ENGLISH_WORDS: set[str] = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her",
    "she", "or", "an", "will", "my", "one", "all", "would", "there",
    "their", "what", "so", "up", "out", "if", "about", "who", "get",
    "which", "go", "me", "when", "make", "can", "like", "time", "no",
    "just", "him", "know", "take", "people", "into", "year", "your",
    "good", "some", "could", "them", "see", "other", "than", "then",
    "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first",
    "well", "way", "even", "new", "want", "because", "any", "these",
    "give", "day", "most", "us", "did", "are", "was", "had", "has",
    "been", "very", "much", "more", "here", "once", "few", "long",
    "may", "still", "too", "must", "should", "need", "yes", "yeah",
    "nah", "okay", "right", "sure", "cool", "great", "nice", "fine",
    "bye", "hey", "hello", "hi", "thanks", "sorry", "please",
    "however", "therefore", "meanwhile", "furthermore", "moreover",
    "appreciate", "understood", "confirmed", "agreed",
    "completely", "obviously", "basically", "honestly", "seriously",
    "exclamation", "hurt", "again", "image", "media", "well",
    "confirm", "merchants", "parliament", "webmaster", "website",
    "youtube", "google", "facebook", "twitter", "instagram", "linkedin",
    "whatsapp", "telegram", "snapchat", "tiktok", "pinterest",
    "quotes", "invoice", "invoicing", "flows", "aqua",
    "soccer", "fifa", "inland", "agency", "human",
    "german", "because", "mac",
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

    # Check against stop word lists (case-sensitive for capitalized forms)
    if trimmed in NLP_STOP_WORDS:
        return False

    # Check lowercase form against rejection lists
    lower = trimmed.lower()
    if entity_type == "ORG" and lower in NOT_ORGS:
        return False
    if entity_type == "PERSON" and lower in NOT_NAMES:
        return False

    # Common English words check (catches sentence-initial caps)
    if " " not in trimmed and lower in COMMON_ENGLISH_WORDS:
        return False

    # Gerund rejection (-ing words as names) — ported from Swift
    if " " not in trimmed and lower.endswith("ing") and len(trimmed) > 4:
        return False

    # Reject multiline entities (NLP sometimes captures across newlines)
    if "\n" in trimmed or "\r" in trimmed:
        return False

    # Multi-word entities starting with a common English word can't be names
    # e.g. "Not Slack", "But Padlis", "For Ocean Love"
    if " " in trimmed and entity_type == "PERSON":
        first_lower = trimmed.split()[0].lower()
        if first_lower in COMMON_ENGLISH_WORDS or first_lower in DETERMINERS:
            return False

    # Nationality/language adjectives are not people
    nationalities = {
        "swiss", "irish", "german", "french", "spanish", "italian",
        "dutch", "swedish", "danish", "norwegian", "finnish", "polish",
        "russian", "chinese", "japanese", "korean", "indian", "brazilian",
        "mexican", "canadian", "australian", "british", "scottish",
        "welsh", "english", "american", "african", "european", "asian",
    }
    if " " not in trimmed and lower in nationalities:
        return False

    # Number words are not people
    number_words = {
        "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty",
        "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
        "hundred", "thousand", "million", "billion",
    }
    if " " not in trimmed and lower in number_words:
        return False

    # Single-word PERSON must be a known first name to avoid false positives
    if entity_type == "PERSON" and " " not in trimmed:
        from .data import COMMON_FIRST_NAMES
        if trimmed not in COMMON_FIRST_NAMES:
            return False

    # Multi-word PERSON: at least one word must be a known first name
    # (prevents "Cash Crusaders", "Fifa Soccer", "Google Flows" etc.)
    if entity_type == "PERSON" and " " in trimmed:
        from .data import COMMON_FIRST_NAMES
        words_list = trimmed.split()
        has_known_name = any(w in COMMON_FIRST_NAMES for w in words_list)
        if not has_known_name:
            return False

    return True


def detect_entities(
    text: str,
    whitelist: set[str],
    already_detected: set[str] | None = None,
) -> list[NLPEntity]:
    """Detect PERSON and ORG entities using pattern matching + validation.

    This is a lightweight NLP layer that finds capitalized word sequences
    and validates them against POS heuristics.

    Args:
        text: Input text to scan.
        whitelist: Uppercased strings to skip.
        already_detected: Lowercased values already detected by earlier layers.
            Used for fragment deduplication (skip substrings of known entities).
    """
    entities: list[NLPEntity] = []
    seen: set[str] = set()
    detected = already_detected or set()

    for m in _CAP_WORD_SEQUENCE_RE.finditer(text):
        value = m.group(1)

        # Skip if in whitelist
        if value.upper() in whitelist:
            continue

        # Skip if already seen
        if value.lower() in seen:
            continue

        # Skip single words that are too short
        words = value.split()
        if len(words) == 1 and len(value) < 3:
            continue

        # Fragment deduplication: skip if this is a substring of an
        # already-detected value (e.g. "Sarah" when "Sarah Chen" exists)
        value_lower = value.lower()
        is_fragment = any(
            value_lower in det and det != value_lower
            for det in detected
        )
        if is_fragment:
            continue

        # Determine type heuristically
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
