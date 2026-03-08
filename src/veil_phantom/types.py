"""
VeilPhantom — Data types for the PII redaction pipeline.
"""

from enum import Enum


class SensitiveTokenType(str, Enum):
    """Token types for redacted sensitive data."""
    PERSON = "PERSON"
    ORG = "ORG"
    LOC = "LOC"
    AMOUNT = "AMOUNT"
    DATE = "DATE"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    PROJECT = "PROJECT"
    NUM = "NUM"
    FINANCIAL = "FINANCIAL"
    SCHEDULE = "SCHEDULE"
    CREDENTIAL = "CREDENTIAL"
    GOVID = "GOVID"
    CARD = "CARD"
    BANKACCT = "BANKACCT"
    IPADDR = "IPADDR"
    ADDRESS = "ADDRESS"
    ROLE = "ROLE"
    SITUATION = "SITUATION"
    TEMPORAL = "TEMPORAL"


class SensitivityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    SAFE = "SAFE"


class DetectionSource(str, Enum):
    SHADE = "Shade"
    REGEX = "Regex"
    CONTEXTUAL = "Context"
    GAZETTEER = "Gazetteer"
    UNKNOWN = "?"


class PhantomPools:
    """Pre-defined phantom values for each entity type (legacy — token-direct is default)."""
    PERSON = ["Alex", "Jordan", "Sam", "Morgan", "Taylor", "Casey", "Riley", "Quinn", "Avery", "Blake", "Drew", "Jamie", "Charlie", "Skyler", "Reese"]
    ORG = ["TechCorp", "GlobalInc", "Acme Industries", "Pinnacle Group", "Vertex Partners", "Summit Holdings", "Atlas Corp", "Nova Systems", "Apex Solutions", "Horizon Ltd"]
    LOC = ["Springfield", "Riverside", "Greenville", "Fairview", "Lakewood", "Hillside", "Brookfield", "Oakdale", "Maplewood", "Clearwater"]
    AMOUNT = ["$1M", "$500K", "$2M", "$5M", "$750K", "$3M", "$100K", "$10M", "$250K", "$1.5M"]
    DATE = ["next month", "last quarter", "Q2", "mid-year", "end of quarter", "next week", "early March", "late April", "fiscal year-end"]
    PHONE = ["555-0100", "555-0200", "555-0300", "555-0400", "555-0500", "555-0600", "555-0700"]
    EMAIL = ["contact@example.com", "info@example.com", "support@example.com", "hello@example.com", "team@example.com"]
    FINANCIAL = ["the investment", "the funding", "the deal", "the transaction", "the agreement"]
    SCHEDULE = ["the meeting", "the deadline", "the milestone", "the launch date"]
    GOVID = ["XX-XXXXX-XX", "000-00-0000", "ID-REDACTED", "GOV-XXXXXX", "DL-000000"]
    CARD = ["4000-0000-0000-0000", "XXXX-XXXX-XXXX-0000", "5500-0000-0000-0000"]
    BANKACCT = ["ACCT-XXXXXXXX", "00-0000-0000", "IBAN-XXXX"]
    IPADDR = ["10.0.0.1", "192.168.0.1", "172.16.0.1", "0.0.0.0"]
    ADDRESS = ["123 Example Street", "456 Main Road", "789 Oak Avenue"]
    ROLE = ["the official", "the executive", "the representative", "the senior leader", "the department head", "the board member", "the director"]
    SITUATION = ["the matter", "the issue", "the ongoing situation", "the internal discussion", "the pending matter", "the confidential topic"]
    TEMPORAL = ["recently", "in the near future", "at that time", "during the period", "ahead of schedule"]

    _MAP: dict = None  # type: ignore

    @classmethod
    def get_pool(cls, token_type: SensitiveTokenType) -> list[str]:
        if cls._MAP is None:
            cls._MAP = {
                SensitiveTokenType.PERSON: cls.PERSON,
                SensitiveTokenType.ORG: cls.ORG,
                SensitiveTokenType.LOC: cls.LOC,
                SensitiveTokenType.AMOUNT: cls.AMOUNT,
                SensitiveTokenType.DATE: cls.DATE,
                SensitiveTokenType.PHONE: cls.PHONE,
                SensitiveTokenType.EMAIL: cls.EMAIL,
                SensitiveTokenType.FINANCIAL: cls.FINANCIAL,
                SensitiveTokenType.SCHEDULE: cls.SCHEDULE,
                SensitiveTokenType.GOVID: cls.GOVID,
                SensitiveTokenType.CARD: cls.CARD,
                SensitiveTokenType.BANKACCT: cls.BANKACCT,
                SensitiveTokenType.IPADDR: cls.IPADDR,
                SensitiveTokenType.ADDRESS: cls.ADDRESS,
                SensitiveTokenType.ROLE: cls.ROLE,
                SensitiveTokenType.SITUATION: cls.SITUATION,
                SensitiveTokenType.TEMPORAL: cls.TEMPORAL,
            }
        return cls._MAP.get(token_type, cls.PERSON)
