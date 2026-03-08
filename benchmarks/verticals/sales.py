"""Sales/CRM vertical — lead management, deal tracking, proposals."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_lead",
            "description": "Create a new sales lead in the CRM.",
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_name": {"type": "string"},
                    "company": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "deal_size": {"type": "string"},
                    "source": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["contact_name", "company"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_deal",
            "description": "Update a deal's status or details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "deal_name": {"type": "string"},
                    "stage": {"type": "string", "enum": ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]},
                    "amount": {"type": "string"},
                    "close_date": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["deal_name", "stage"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_proposal",
            "description": "Send a sales proposal to a prospect.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_name": {"type": "string"},
                    "recipient_email": {"type": "string"},
                    "company": {"type": "string"},
                    "proposal_value": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["recipient_name", "recipient_email", "proposal_value"],
            },
        },
    },
]

SCENARIOS = [
    {
        "name": "Conference Lead",
        "instruction": "Create a lead from this conference follow-up note.",
        "input": (
            "Met Kenji Yamamoto at the Johannesburg AI Summit. He's VP of Product at Rakuten. "
            "Interested in our privacy SDK for their payments platform. Potential deal: $2.4M ARR. "
            "His card: kenji.yamamoto@rakuten.co.jp, +81 3 4567 8901. "
            "He mentioned their CTO Yuki Sato is the final decision-maker."
        ),
        "expected_tools": ["create_lead"],
        "pii_entities": ["Kenji Yamamoto", "Rakuten", "kenji.yamamoto@rakuten.co.jp", "+81 3 4567 8901",
                         "$2.4M", "Yuki Sato"],
    },
    {
        "name": "Deal Progression",
        "instruction": "Update the deal and send a proposal based on this sales call summary.",
        "input": (
            "Great call with Linda Khumalo at Discovery Health. They want to move forward with "
            "the enterprise plan. Deal value: R4.8 million/year. Move to proposal stage. "
            "Send the proposal to linda.khumalo@discovery.co.za. "
            "Close date target: April 30th. She needs it approved by CEO Adrian Gore."
        ),
        "expected_tools": ["update_deal", "send_proposal"],
        "pii_entities": ["Linda Khumalo", "Discovery Health", "R4.8 million", "linda.khumalo@discovery.co.za",
                         "Adrian Gore"],
    },
    {
        "name": "Lost Deal Analysis",
        "instruction": "Update this deal as lost and create a lead for the alternative contact.",
        "input": (
            "Lost the Barclays Africa deal — David Rothenberg chose a competitor. "
            "Deal was worth $1.2M. However, his colleague Zanele Mbeki from the Cape Town office "
            "is interested in a smaller pilot. Contact: zanele.mbeki@barclays.co.za, +27 21 555 4432. "
            "Potential pilot value: $180K."
        ),
        "expected_tools": ["update_deal", "create_lead"],
        "pii_entities": ["David Rothenberg", "Barclays Africa", "$1.2M", "Zanele Mbeki",
                         "zanele.mbeki@barclays.co.za", "+27 21 555 4432", "$180K"],
    },
]
