"""Financial services vertical — fund transfers, invoicing, expense reports."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "transfer_funds",
            "description": "Initiate a fund transfer between accounts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_account": {"type": "string", "description": "Source account"},
                    "to_account": {"type": "string", "description": "Destination account"},
                    "amount": {"type": "string", "description": "Transfer amount"},
                    "currency": {"type": "string", "description": "Currency code"},
                    "reference": {"type": "string", "description": "Payment reference"},
                },
                "required": ["from_account", "to_account", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_invoice",
            "description": "Create an invoice for a client.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string"},
                    "client_email": {"type": "string"},
                    "amount": {"type": "string"},
                    "description": {"type": "string"},
                    "due_date": {"type": "string"},
                },
                "required": ["client_name", "amount", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_expense",
            "description": "Submit an expense report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee": {"type": "string"},
                    "amount": {"type": "string"},
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "receipt_id": {"type": "string"},
                },
                "required": ["employee", "amount", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flag_transaction",
            "description": "Flag a suspicious transaction for review.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {"type": "string"},
                    "account": {"type": "string"},
                    "reason": {"type": "string"},
                    "amount": {"type": "string"},
                },
                "required": ["account", "reason"],
            },
        },
    },
]

SCENARIOS = [
    {
        "name": "Wire Transfer",
        "instruction": "Process this wire transfer request.",
        "input": (
            "Please wire R2.5 million from Standard Bank account 62847501234 to "
            "IBAN GB29 NWBK 6016 1331 9268 19. Reference: INV-2024-Q3. "
            "This is for the Johnson & Partners consulting fee."
        ),
        "expected_tools": ["transfer_funds"],
        "pii_entities": ["R2.5 million", "62847501234", "GB29 NWBK 6016 1331 9268 19", "Johnson & Partners"],
    },
    {
        "name": "Client Invoice",
        "instruction": "Create an invoice based on this meeting note.",
        "input": (
            "Wrap up with Priya Sharma at Tata Consulting. Bill them $47,500 for the Phase 2 "
            "data migration project. Her email is priya.sharma@tataconsulting.com. "
            "Net 30 terms, due April 15th 2026."
        ),
        "expected_tools": ["create_invoice"],
        "pii_entities": ["Priya Sharma", "Tata Consulting", "$47,500", "priya.sharma@tataconsulting.com"],
    },
    {
        "name": "Expense Report",
        "instruction": "Submit this expense report for the employee.",
        "input": (
            "James Okafor spent $3,200 on client dinners during the Lagos trip. "
            "Credit card ending 4829. Receipt #REC-20260301. Also $1,850 for the Uber "
            "Black from OR Tambo to the Sandton office. His employee ID is EMP-4521."
        ),
        "expected_tools": ["submit_expense"],
        "pii_entities": ["James Okafor", "$3,200", "4829", "$1,850"],
    },
    {
        "name": "Suspicious Activity",
        "instruction": "Review this and flag any suspicious transactions.",
        "input": (
            "Account 7789234561 belonging to Chen Wei has three outbound wires totaling "
            "$890,000 in 24 hours to accounts in the Cayman Islands. Account holder's "
            "ID number is 850612 5234 083. Contact the compliance team at "
            "compliance@meridianbank.co.za immediately."
        ),
        "expected_tools": ["flag_transaction"],
        "pii_entities": ["7789234561", "Chen Wei", "$890,000", "850612 5234 083", "compliance@meridianbank.co.za"],
    },
]
