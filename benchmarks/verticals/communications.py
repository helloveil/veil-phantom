"""Communications vertical — emails, meeting scheduling, memos."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "cc": {"type": "array", "items": {"type": "string"}},
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
                    "duration": {"type": "string"},
                    "agenda": {"type": "string"},
                    "location": {"type": "string"},
                },
                "required": ["participants", "date", "agenda"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create an action item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "assignee": {"type": "string"},
                    "deadline": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "description": {"type": "string"},
                },
                "required": ["title", "assignee"],
            },
        },
    },
]

SCENARIOS = [
    {
        "name": "Meeting Follow-up",
        "instruction": "Send a follow-up email and create action items from this meeting transcript.",
        "input": (
            "Board meeting with CEO Amanda Torres, CFO Brian Walsh, and CTO Lisa Park. "
            "Key decisions: 1) Approve $45M Series C at $200M valuation. "
            "2) Brian to finalize term sheet by March 15th. "
            "3) Lisa to complete security audit before investor demo. "
            "Send summary to all three. Amanda: a.torres@company.com, "
            "Brian: b.walsh@company.com, Lisa: l.park@company.com."
        ),
        "expected_tools": ["send_email", "create_task"],
        "pii_entities": ["Amanda Torres", "Brian Walsh", "Lisa Park", "$45M", "$200M",
                         "a.torres@company.com", "b.walsh@company.com", "l.park@company.com"],
    },
    {
        "name": "Client Meeting Setup",
        "instruction": "Schedule this meeting and send a confirmation email to the client.",
        "input": (
            "Need to set up a demo with Ravi Krishnan from Infosys. He's available Thursday at "
            "2 PM SAST. His team (Priya Nair and Amit Shah) should also attend. "
            "Location: Sandton City office, 5th floor boardroom. "
            "Ravi's email: ravi.krishnan@infosys.com. Confirm the meeting and send agenda."
        ),
        "expected_tools": ["schedule_meeting", "send_email"],
        "pii_entities": ["Ravi Krishnan", "Infosys", "Priya Nair", "Amit Shah",
                         "ravi.krishnan@infosys.com", "Sandton City"],
    },
    {
        "name": "Urgent Memo",
        "instruction": "Send an urgent internal email based on this situation.",
        "input": (
            "Security incident: unauthorized access detected on server prod-db-03 at 03:45 AM. "
            "IP address 192.168.1.105 attempted to access customer database containing "
            "450,000 records. CISO Daniel Botha needs to be notified immediately at "
            "d.botha@company.co.za. Also notify the DPO at dpo@company.co.za. "
            "Incident reference: SEC-2026-0042."
        ),
        "expected_tools": ["send_email"],
        "pii_entities": ["Daniel Botha", "d.botha@company.co.za", "dpo@company.co.za", "192.168.1.105"],
    },
]
