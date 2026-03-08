"""
VeilPhantom — All compiled regex patterns.
Ported from RedactionPatterns.swift.
"""

import re

# MARK: - Money/Amount Patterns

USD = re.compile(
    r"\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand|k|m|b)\b)?",
    re.IGNORECASE,
)

RAND_PREFIX = re.compile(
    r"\bR\s?[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand|k|m|b)\b)?",
    re.IGNORECASE,
)

RAND_SUFFIX = re.compile(
    r"\b\d+(?:[\d,\.]+)?\s*(?:million|billion|thousand|k|m|b)?\s*(?:rand|rands|zar)[A-Za-z]?\b",
    re.IGNORECASE,
)

_NUM_WORD = r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)"
_NUM_WORD_CHAIN = (
    r"(?:" + _NUM_WORD + r"(?:[\s-]+(?:and[\s-]+)?" + _NUM_WORD + r")?"
    r"(?:[\s-]+point[\s-]+(?:one|two|three|four|five|six|seven|eight|nine|zero)"
    r"(?:[\s-]+(?:one|two|three|four|five|six|seven|eight|nine|zero))*)?"
    r"(?:[\s-]+hundred)?"
    r"(?:[\s-]+(?:and[\s-]+)?(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)"
    r"(?:[\s-]+(?:one|two|three|four|five|six|seven|eight|nine))?)?)"
)

VERBAL_AMOUNT = re.compile(
    r"\b" + _NUM_WORD_CHAIN + r"\s+(?:thousand|million|billion)"
    r"(?:\s+(?:rand|rands|dollars?|euros?|pounds?))?\b",
    re.IGNORECASE,
)

BARE_NUMERIC_AMOUNT = re.compile(
    r"\b\d+(?:[\d,\.]+)?\s+(?:million|billion|thousand)\b",
    re.IGNORECASE,
)

# MARK: - Phone Patterns

PHONE_INTL = re.compile(r"\+\d{1,3}\s?\d{2}\s?\d{3}\s?\d{4}")
PHONE_SA = re.compile(r"0[78]\d[-.\s]?\d{3}[-.\s]?\d{4}")
PHONE_LOCAL = re.compile(r"0\d{2}[-.\s]?\d{3}[-.\s]?\d{4}")
PHONE_US = re.compile(r"\+?1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")

# Spoken-form patterns
_DIGIT_WORD = r"(?:zero|oh|one|two|three|four|five|six|seven|eight|nine)"
SPOKEN_PHONE = re.compile(
    r"\bplus\s+" + _DIGIT_WORD + r"(?:\s+" + _DIGIT_WORD + r"){6,12}\b",
    re.IGNORECASE,
)
SPOKEN_BANK_ACCOUNT = re.compile(
    r"(?:account\s*(?:number|no|num)?\.?\s*(?:is|:)?\s*)"
    + _DIGIT_WORD + r"(?:\s+" + _DIGIT_WORD + r"){7,16}\b",
    re.IGNORECASE,
)
SPOKEN_GOV_ID = re.compile(
    r"(?:(?:ID|identity|identification)\s*(?:number|no|num)?\.?\s*(?:is|:)?\s*)"
    + _DIGIT_WORD + r"(?:\s+" + _DIGIT_WORD + r"){10,14}\b",
    re.IGNORECASE,
)

# MARK: - Email Patterns

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SPOKEN_EMAIL = re.compile(
    r"\b(?!(?:her|his|him|them|their|our|its|the|and|for|but|not|are|was|has|had|get|got|set|let|put|sit|sat|ran|run|hit|cut|bit|did|met|won|ate)\s+at\b)[A-Za-z0-9._%+-]{2,}\s+at\s+[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*\s+dot\s+(?:com|org|net|io|co|ai|dev|app)\b",
    re.IGNORECASE,
)
HYBRID_EMAIL = re.compile(
    r"\b(?!(?:her|his|him|them|their|our|its|the|and|for|but|not|are|was|has|had|get|got|set|let|put|sit|sat|ran|run|hit|cut|bit|did|met|won|ate)\s+at\b)[A-Za-z0-9._%+-]{2,}\s+at\s+[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)

# MARK: - Date Patterns

DATE_MONTH = re.compile(
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?",
    re.IGNORECASE,
)
DATE_NUMERIC = re.compile(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}")
DATE_RELATIVE = re.compile(
    r"(?:next|last|this)\s+(?:week|month|quarter|year|Monday|Tuesday|Wednesday|Thursday|Friday)",
    re.IGNORECASE,
)
SPOKEN_DATE = re.compile(
    r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)"
    r"\s+(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|"
    r"thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|"
    r"twenty[\s-]?first|twenty[\s-]?second|twenty[\s-]?third|twenty[\s-]?fourth|"
    r"twenty[\s-]?fifth|twenty[\s-]?sixth|twenty[\s-]?seventh|twenty[\s-]?eighth|"
    r"twenty[\s-]?ninth|thirtieth|thirty[\s-]?first)"
    r"(?:[\s,]+(?:twenty\s+)?(?:twenty|nineteen)\s+(?:one|two|three|four|five|six|seven|eight|nine|"
    r"ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"twenty[\s-]?(?:one|two|three|four|five|six|seven|eight|nine)))?\b",
    re.IGNORECASE,
)

# MARK: - Government ID Patterns

SSN = re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b")
SA_ID = re.compile(r"\b\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{4}[01]\d{2}\b")
PASSPORT = re.compile(
    r"(?:passport\s*(?:number|no|#|num)?\.?\s*(?:is|:)?\s*)([A-Z]?\d{6,9})",
    re.IGNORECASE,
)
DRIVERS_LICENSE = re.compile(
    r"(?:(?:driver'?s?\s*)?licen[sc]e\s*(?:number|no|#|num)?\.?\s*(?:is|:)?\s*)([A-Z]?\d{5,12})",
    re.IGNORECASE,
)

# MARK: - Financial Instrument Patterns

CREDIT_CARD = re.compile(r"\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{3,4}\b")
BANK_ACCOUNT = re.compile(
    r"(?:account\s*(?:number|no|#|num)?\.?\s*(?:is|:)?\s*)(\d{8,17})",
    re.IGNORECASE,
)
IBAN = re.compile(r"\b[A-Z]{2}\d{2}[\s]?[A-Z0-9]{4}[\s]?(?:[A-Z0-9]{4}[\s]?){1,7}[A-Z0-9]{1,4}\b")

# MARK: - Network/Address Patterns

IPV4 = re.compile(
    r"\b(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\."
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
STREET_ADDRESS = re.compile(
    r"\b\d{1,5}\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?\s+"
    r"(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Boulevard|Blvd|Lane|Ln|Way|Place|Pl|Court|Ct|Terrace|Circle|Crescent)\b"
)

# MARK: - Contextual Sensitivity Patterns (V9)

IDENTIFYING_ROLE = re.compile(
    r"\b(?:the\s+)?(?:Secretary|Ambassador|Minister|Deputy\s+(?:Minister|Secretary|Director)|"
    r"Prime\s+Minister|President|Vice\s+President|Chairman|Chairwoman|"
    r"Chief\s+(?:Executive|Operating|Financial|Technology|Marketing)\s+Officer|"
    r"CEO|CFO|CTO|COO|CMO|General\s+Counsel|Chief\s+of\s+Staff|Commissioner|"
    r"Director\s+General|Permanent\s+Secretary|Under\s+Secretary|Special\s+Envoy|"
    r"Consul|Attaché|Governor|Lieutenant\s+Governor|Mayor|Senator|Congressman|"
    r"Congresswoman|Representative|Judge|Justice|Attorney\s+General|"
    r"Solicitor\s+General|Prosecutor|Ombudsman|Auditor\s+General|Inspector\s+General)"
    r"(?:\s+of\s+[A-Z][a-zA-Z\s]+)?\b",
    re.IGNORECASE,
)

SENSITIVE_SITUATION = re.compile(
    r"\b(?:corruption\s+(?:allegations?|charges?|scandal|investigation|probe)|"
    r"bribery\s+(?:allegations?|charges?|scandal)|"
    r"fraud\s+(?:allegations?|charges?|investigation)|"
    r"sexual\s+(?:harassment|assault|misconduct)\s+(?:allegations?|charges?|claims?)|"
    r"whistleblower|"
    r"pending\s+(?:acquisition|merger|IPO|lawsuit|investigation|indictment|charges?)|"
    r"secret(?:ly)?\s+(?:meeting|negotiation|deal|agreement)|"
    r"confidential\s+(?:settlement|agreement|negotiation)|"
    r"insider\s+(?:trading|information)|material\s+non-public\s+information|MNPI|"
    r"undisclosed\s+(?:relationship|conflict|interest)|"
    r"off-the-record|embargoed|"
    r"classified\s+(?:information|documents?|briefing)|"
    r"security\s+(?:breach|clearance|incident)|data\s+(?:breach|leak)|"
    r"leak(?:ed)?\s+(?:documents?|information|memo)|"
    r"unauthorized\s+(?:disclosure|access)|"
    r"disciplinary\s+(?:action|hearing|proceedings?)|"
    r"termination\s+(?:hearing|proceedings?)|"
    r"misconduct\s+(?:allegations?|investigation)|"
    r"ethics\s+(?:violation|complaint|investigation)|"
    r"conflict\s+of\s+interest|"
    r"regulatory\s+(?:violation|investigation|action)|"
    r"compliance\s+(?:violation|breach|investigation))\b",
    re.IGNORECASE,
)

TEMPORAL_SENSITIVITY = re.compile(
    r"\b(?:before\s+(?:the\s+)?(?:announcement|public\s+(?:announcement|disclosure|release)|"
    r"it\s+(?:went|goes|becomes?)\s+public|earnings?\s+(?:call|release|report)|"
    r"IPO|filing|press\s+release|shareholder\s+meeting)|"
    r"ahead\s+of\s+(?:the\s+)?(?:announcement|earnings?|IPO|filing|public\s+(?:disclosure|release))|"
    r"prior\s+to\s+(?:public\s+)?(?:disclosure|announcement|release)|"
    r"embargoed?\s+until|"
    r"not\s+(?:yet\s+)?(?:public|announced|disclosed|released)|"
    r"under\s+embargo|pre-(?:announcement|earnings|IPO|release)|"
    r"during\s+(?:the\s+)?(?:quiet|blackout)\s+period|"
    r"in\s+confidence|off\s+the\s+record|"
    r"not\s+for\s+(?:public\s+)?(?:distribution|release|disclosure))\b",
    re.IGNORECASE,
)

UNIQUE_DESCRIPTOR = re.compile(
    r"\b(?:the\s+(?:only|sole|single|first|youngest|oldest|last|lone|unique)\s+"
    r"[a-zA-Z]+(?:\s+[a-zA-Z]+)?\s+(?:who|that|with|from|in|at)|"
    r"the\s+(?:patient|client|employee|candidate|applicant|defendant|plaintiff|witness|victim|suspect|accused)\s+"
    r"(?:with\s+(?:the\s+)?(?:rare|unusual|unique|specific)|"
    r"from\s+(?:last\s+)?(?:Tuesday|Wednesday|Thursday|Friday|Monday|Saturday|Sunday|week|month)|"
    r"in\s+(?:the\s+)?(?:case|matter|incident))|"
    r"the\s+(?:rare|unusual|unique|specific)\s+(?:condition|case|situation|circumstance|disease|disorder|syndrome))\b",
    re.IGNORECASE,
)

# MARK: - Financial Institution Patterns (V12)

FINANCIAL_INSTITUTIONS = re.compile(
    r"\b(?:first national bank|standard bank|absa|nedbank|fnb|capitec|investec|"
    r"african bank|discovery bank|tyme bank|bank zero|old mutual|sanlam|liberty|"
    r"allan gray|coronation|goldman sachs|jp morgan|morgan stanley|deutsche bank)\b",
    re.IGNORECASE,
)

INVESTMENT_FIRM = re.compile(
    r"\b[A-Z][a-zA-Z]*(?:\s+[a-zA-Z]+)?\s+(?:tech\s+)?(?:ventures|capital|partners|"
    r"investments|holdings|advisors|securities|asset\s+management)\b",
    re.IGNORECASE,
)

# MARK: - URL/Domain Patterns (V22)

URL_DOMAIN = re.compile(
    r"(?:https?://)?(?:www\.)?[a-zA-Z0-9][\w.-]*\.(?:com|co\.za|org|net|io|dev|app|ai|co|biz|info|me|tech|agency|digital|online|store|shop|site|xyz|africa)\b(?:/[\w./?%&=-]*)?",
    re.IGNORECASE,
)

SAFE_DOMAINS: set[str] = {
    "google.com", "youtube.com", "facebook.com", "instagram.com",
    "twitter.com", "linkedin.com", "github.com", "wordpress.com",
    "shopify.com", "monday.com", "slack.com", "notion.com",
    "whatsapp.com", "zoom.us", "microsoft.com", "apple.com",
    "amazon.com", "stripe.com", "squarespace.com", "wix.com",
    "mailchimp.com", "hubspot.com", "canva.com", "figma.com",
    "semrush.com", "ahrefs.com", "moz.com", "cloudflare.com",
    "vercel.com", "netlify.com", "heroku.com", "digitalocean.com",
    "openai.com", "anthropic.com", "stackoverflow.com", "npmjs.com",
    "googleapis.com", "gstatic.com", "googleusercontent.com",
    "w3.org", "schema.org", "wikipedia.org", "mozilla.org",
}
