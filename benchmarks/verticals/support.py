"""Customer support vertical — ticket handling, escalations, refunds."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create a support ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string"},
                    "customer_email": {"type": "string"},
                    "subject": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "category": {"type": "string"},
                },
                "required": ["customer_name", "subject", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "Process a customer refund.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string"},
                    "order_id": {"type": "string"},
                    "amount": {"type": "string"},
                    "reason": {"type": "string"},
                    "refund_method": {"type": "string"},
                },
                "required": ["customer_name", "amount", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_ticket",
            "description": "Escalate a ticket to a senior agent or manager.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "escalate_to": {"type": "string"},
                    "reason": {"type": "string"},
                    "customer_name": {"type": "string"},
                },
                "required": ["escalate_to", "reason"],
            },
        },
    },
]

SCENARIOS = [
    {
        "name": "Billing Dispute",
        "instruction": "Handle this customer billing complaint — create a ticket and process the refund.",
        "input": (
            "Customer Grace Nkomo called about being double-charged $299.99 on her credit card "
            "ending 7823. Order #ORD-2026-45891. She's been a customer for 3 years. "
            "Email: grace.nkomo@gmail.com. Phone: +27 82 991 3345. "
            "She wants a refund to her original payment method."
        ),
        "expected_tools": ["create_ticket", "process_refund"],
        "pii_entities": ["Grace Nkomo", "$299.99", "7823", "grace.nkomo@gmail.com", "+27 82 991 3345"],
    },
    {
        "name": "Service Outage Escalation",
        "instruction": "Create a critical ticket and escalate based on this customer report.",
        "input": (
            "Enterprise customer Absa Group (contact: Mohammed Ismail, CTO) reporting complete "
            "API outage since 14:30 SAST. Affecting 50,000+ transactions. "
            "SLA breach imminent — their contract guarantees 99.99% uptime. "
            "Contract value: R12M/year. Escalate to VP Engineering immediately. "
            "Mohammed's direct line: +27 11 350 4000, m.ismail@absa.co.za."
        ),
        "expected_tools": ["create_ticket", "escalate_ticket"],
        "pii_entities": ["Absa Group", "Mohammed Ismail", "R12M", "+27 11 350 4000", "m.ismail@absa.co.za"],
    },
    {
        "name": "Product Return",
        "instruction": "Process this return and refund request.",
        "input": (
            "Anele Zulu wants to return 3 units of the Pro Plan license purchased on Feb 28th. "
            "Order #ORD-2026-51234. Total refund: $897. Reason: switching to competitor. "
            "Refund to bank account FNB 6245 7890 123. Email: anele@techstartup.co.za."
        ),
        "expected_tools": ["process_refund"],
        "pii_entities": ["Anele Zulu", "$897", "6245 7890 123", "anele@techstartup.co.za"],
    },
]
