"""Legal vertical — contract review, compliance, case management."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_case",
            "description": "Create a new legal case or matter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_title": {"type": "string"},
                    "client_name": {"type": "string"},
                    "case_type": {"type": "string"},
                    "opposing_party": {"type": "string"},
                    "assigned_attorney": {"type": "string"},
                    "court": {"type": "string"},
                    "filing_deadline": {"type": "string"},
                },
                "required": ["case_title", "client_name", "case_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_contract_clause",
            "description": "Draft or modify a contract clause.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_id": {"type": "string"},
                    "clause_type": {"type": "string"},
                    "parties": {"type": "array", "items": {"type": "string"}},
                    "terms": {"type": "string"},
                },
                "required": ["clause_type", "parties", "terms"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_compliance_report",
            "description": "File a regulatory compliance report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "regulation": {"type": "string"},
                    "findings": {"type": "string"},
                    "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "deadline": {"type": "string"},
                },
                "required": ["company", "regulation", "findings"],
            },
        },
    },
]

SCENARIOS = [
    {
        "name": "New Litigation",
        "instruction": "Create a new case based on this intake note.",
        "input": (
            "New matter: Sipho Nkosi is suing GlobalTech SA (Pty) Ltd for wrongful dismissal. "
            "Case to be filed in the Johannesburg Labour Court. Case number LC-2026-0312. "
            "Sipho's ID: 890412 5123 087. His attorney is Adv. Rebecca van der Merwe from "
            "Norton Rose Fulbright. Filing deadline: March 30th 2026. "
            "Sipho worked there 8 years, last salary R85,000/month."
        ),
        "expected_tools": ["create_case"],
        "pii_entities": ["Sipho Nkosi", "GlobalTech SA", "890412 5123 087", "Adv. Rebecca van der Merwe",
                         "Norton Rose Fulbright", "R85,000", "LC-2026-0312"],
    },
    {
        "name": "NDA Clause",
        "instruction": "Draft an NDA clause based on this deal discussion.",
        "input": (
            "We need a mutual NDA between Veil Technologies and Samsung Electronics. "
            "The NDA should cover the AI privacy partnership discussions. Duration: 3 years. "
            "Signed by Nakai Williams (CEO, Veil) and Park Joon-ho (VP Innovation, Samsung). "
            "Contact: nakai@helloveil.com and joonho.park@samsung.com."
        ),
        "expected_tools": ["draft_contract_clause"],
        "pii_entities": ["Nakai Williams", "Park Joon-ho", "nakai@helloveil.com", "joonho.park@samsung.com",
                         "Veil Technologies", "Samsung Electronics"],
    },
    {
        "name": "POPIA Compliance",
        "instruction": "File a compliance report based on this audit finding.",
        "input": (
            "Audit of MediCare Holdings revealed POPIA violations: unencrypted patient data "
            "for 12,000 patients stored on an exposed S3 bucket. CTO James Fletcher confirmed "
            "the breach occurred between January 5-12, 2026. Affected data includes ID numbers, "
            "medical records, and contact details. The Information Regulator must be notified "
            "within 72 hours. Contact: j.fletcher@medicare.co.za, +27 11 555 8901."
        ),
        "expected_tools": ["file_compliance_report"],
        "pii_entities": ["MediCare Holdings", "James Fletcher", "j.fletcher@medicare.co.za", "+27 11 555 8901"],
    },
]
