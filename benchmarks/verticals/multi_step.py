"""Multi-step workflows — complex scenarios requiring 3+ tool calls and reasoning."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_contact",
            "description": "Look up a contact's information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_meeting",
            "description": "Schedule a meeting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "participants": {"type": "array", "items": {"type": "string"}},
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                    "agenda": {"type": "string"},
                },
                "required": ["participants", "date", "agenda"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "assignee": {"type": "string"},
                    "deadline": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                },
                "required": ["title", "assignee"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_funds",
            "description": "Process a payment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_account": {"type": "string"},
                    "to_account": {"type": "string"},
                    "amount": {"type": "string"},
                    "reference": {"type": "string"},
                },
                "required": ["to_account", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_document",
            "description": "Create a document or report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "doc_type": {"type": "string"},
                    "recipients": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "content"],
            },
        },
    },
]

SCENARIOS = [
    {
        "name": "Acquisition Workflow",
        "instruction": "Process this acquisition: look up the contacts, schedule the signing meeting, create due diligence tasks, and initiate the deposit transfer.",
        "input": (
            "We're acquiring TechStart Inc for $8.5M. Signing meeting next Friday at 10 AM with "
            "their CEO Jack Morrison and our lawyer Adv. Thandi Mkhize. "
            "Transfer the $850K deposit (10%) to TechStart's account IBAN DE89 3704 0044 0532 0130 00. "
            "Our account: FNB 6234 5678 901. Reference: ACQ-TECHSTART-2026. "
            "Tasks: 1) Thandi to complete IP review by Wednesday, "
            "2) CFO Sarah Chen to verify financials by Thursday. "
            "Contact Jack at jack@techstart.io."
        ),
        "expected_tools": ["lookup_contact", "schedule_meeting", "create_task", "transfer_funds"],
        "pii_entities": ["Jack Morrison", "Adv. Thandi Mkhize", "$8.5M", "$850K",
                         "DE89 3704 0044 0532 0130 00", "6234 5678 901", "Sarah Chen",
                         "jack@techstart.io", "TechStart Inc"],
    },
    {
        "name": "Investor Update",
        "instruction": "Create a quarterly investor update document, email it to investors, and schedule the next board meeting.",
        "input": (
            "Q4 results: Revenue $12.3M (up 34%), 850 enterprise customers, ARR $45M. "
            "Key wins: signed Vodacom ($2.1M deal, contact Sihle Dlamini s.dlamini@vodacom.co.za) "
            "and Standard Bank ($3.4M, contact Peter Wright p.wright@standardbank.co.za). "
            "Send update to lead investor Michael Park at m.park@sequoia.com. "
            "Schedule Q1 board meeting for April 15th with Michael, "
            "our CEO Amanda Torres, and CFO Brian Walsh."
        ),
        "expected_tools": ["create_document", "send_email", "schedule_meeting"],
        "pii_entities": ["$12.3M", "$45M", "Sihle Dlamini", "s.dlamini@vodacom.co.za",
                         "$2.1M", "Peter Wright", "p.wright@standardbank.co.za", "$3.4M",
                         "Michael Park", "m.park@sequoia.com", "Amanda Torres", "Brian Walsh"],
    },
    {
        "name": "Incident Response",
        "instruction": "Handle this security incident: create tasks for each team member, email the affected client, and schedule an emergency meeting.",
        "input": (
            "Critical: Data breach detected at 2:30 AM. Client Absa Group affected — "
            "contact their CISO Fumani Mthembu at f.mthembu@absa.co.za (+27 11 350 4567). "
            "Tasks: 1) CISO Daniel Botha — forensic analysis by EOD (critical), "
            "2) Legal counsel Advocate Precious Moloi — prepare breach notification (high), "
            "3) CTO Lisa Park — patch vulnerability CVE-2026-1234 (critical). "
            "Emergency meeting tomorrow at 8 AM with all three plus CEO Amanda Torres. "
            "Incident ref: SEC-2026-0089."
        ),
        "expected_tools": ["create_task", "send_email", "schedule_meeting"],
        "pii_entities": ["Absa Group", "Fumani Mthembu", "f.mthembu@absa.co.za", "+27 11 350 4567",
                         "Daniel Botha", "Advocate Precious Moloi", "Lisa Park", "Amanda Torres"],
    },
]
