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
        "expected_args": {
            "create_lead": {
                "contact_name": lambda v: "Kenji Yamamoto" in v or "[PERSON_" in v,
                "company": lambda v: "Rakuten" in v or "[ORG_" in v,
                "email": lambda v: "kenji.yamamoto@rakuten.co.jp" in v or "[EMAIL_" in v,
                "phone": lambda v: "+81 3 4567 8901" in v or "[PHONE_" in v,
                "deal_size": lambda v: "$2.4M" in v or "2.4" in v or "[AMOUNT_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Kenji Yamamoto", "Yuki Sato"],
            "ORG": ["Rakuten"],
            "EMAIL": ["kenji.yamamoto@rakuten.co.jp"],
            "PHONE": ["+81 3 4567 8901"],
            "AMOUNT": ["$2.4M"],
        },
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
        "expected_args": {
            "update_deal": {
                "deal_name": lambda v: "Discovery" in v or "[ORG_" in v,
                "stage": lambda v: v == "proposal",
                "amount": lambda v: "4.8" in v or "[AMOUNT_" in v,
                "close_date": lambda v: "April" in v or "04" in v or "30" in v,
            },
            "send_proposal": {
                "recipient_name": lambda v: "Linda Khumalo" in v or "[PERSON_" in v,
                "recipient_email": lambda v: "linda.khumalo@discovery.co.za" in v or "[EMAIL_" in v,
                "proposal_value": lambda v: "4.8" in v or "[AMOUNT_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Linda Khumalo", "Adrian Gore"],
            "ORG": ["Discovery Health"],
            "EMAIL": ["linda.khumalo@discovery.co.za"],
            "AMOUNT": ["R4.8 million"],
        },
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
        "expected_args": {
            "update_deal": {
                "deal_name": lambda v: "Barclays" in v or "[ORG_" in v,
                "stage": lambda v: v == "closed_lost",
                "amount": lambda v: "1.2M" in v or "[AMOUNT_" in v,
            },
            "create_lead": {
                "contact_name": lambda v: "Zanele Mbeki" in v or "[PERSON_" in v,
                "company": lambda v: "Barclays" in v or "[ORG_" in v,
                "email": lambda v: "zanele.mbeki@barclays.co.za" in v or "[EMAIL_" in v,
                "phone": lambda v: "+27 21 555 4432" in v or "[PHONE_" in v,
                "deal_size": lambda v: "180K" in v or "[AMOUNT_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["David Rothenberg", "Zanele Mbeki"],
            "ORG": ["Barclays Africa"],
            "EMAIL": ["zanele.mbeki@barclays.co.za"],
            "PHONE": ["+27 21 555 4432"],
            "AMOUNT": ["$1.2M", "$180K"],
        },
    },
    {
        "name": "Enterprise Upsell",
        "instruction": "Update the deal for the contract expansion and send a renewal proposal.",
        "input": (
            "Fantastic news — Priya Venkatesh at Infosys confirmed they want to expand from 500 to "
            "2,000 seats. Current contract ends June 15th. New deal value: $3.6M/year, up from $900K. "
            "Priya's direct line: +91 80 6123 4567. Email: priya.venkatesh@infosys.com. "
            "Their procurement lead Arjun Desai (arjun.desai@infosys.com) needs to co-sign. "
            "Move to negotiation stage. Send the renewal proposal to Priya."
        ),
        "expected_tools": ["update_deal", "send_proposal"],
        "expected_args": {
            "update_deal": {
                "deal_name": lambda v: "Infosys" in v or "[ORG_" in v,
                "stage": lambda v: v == "negotiation",
                "amount": lambda v: "3.6M" in v or "[AMOUNT_" in v,
                "close_date": lambda v: "June" in v or "06" in v or "15" in v,
            },
            "send_proposal": {
                "recipient_name": lambda v: "Priya Venkatesh" in v or "[PERSON_" in v,
                "recipient_email": lambda v: "priya.venkatesh@infosys.com" in v or "[EMAIL_" in v,
                "proposal_value": lambda v: "3.6M" in v or "[AMOUNT_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Priya Venkatesh", "Arjun Desai"],
            "ORG": ["Infosys"],
            "EMAIL": ["priya.venkatesh@infosys.com", "arjun.desai@infosys.com"],
            "PHONE": ["+91 80 6123 4567"],
            "AMOUNT": ["$3.6M", "$900K"],
        },
    },
    {
        "name": "Partner Referral",
        "instruction": "Create a lead from this partner referral with commission details.",
        "input": (
            "Referral from our channel partner Deloitte Brazil. Contact: Mariana Costa e Silva, "
            "Head of Data Privacy at Petrobras. She's looking for a full platform deployment — "
            "estimated deal: R$12 million. Mariana's email: mariana.costa@petrobras.com.br, "
            "phone: +55 21 3224 8800. Referral commission to Deloitte: 12%. "
            "Partner contact: Felipe Andrade (felipe.andrade@deloitte.com.br). "
            "Mariana's CPF on file: 142.567.890-33."
        ),
        "expected_tools": ["create_lead"],
        "expected_args": {
            "create_lead": {
                "contact_name": lambda v: "Mariana Costa e Silva" in v or "[PERSON_" in v,
                "company": lambda v: "Petrobras" in v or "[ORG_" in v,
                "email": lambda v: "mariana.costa@petrobras.com.br" in v or "[EMAIL_" in v,
                "phone": lambda v: "+55 21 3224 8800" in v or "[PHONE_" in v,
                "deal_size": lambda v: "12 million" in v or "12M" in v or "[AMOUNT_" in v,
                "source": lambda v: "Deloitte" in v or "partner" in v.lower() or "[ORG_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Mariana Costa e Silva", "Felipe Andrade"],
            "ORG": ["Deloitte Brazil", "Petrobras"],
            "EMAIL": ["mariana.costa@petrobras.com.br", "felipe.andrade@deloitte.com.br"],
            "PHONE": ["+55 21 3224 8800"],
            "AMOUNT": ["R$12 million"],
            "ID": ["142.567.890-33"],
        },
    },
    {
        "name": "Competitive Win",
        "instruction": "Update this deal as won against the competitor with final contract details.",
        "input": (
            "We won the TotalEnergies deal against Palantir! Contract signed by CFO Nathalie Dupont. "
            "Final value: EUR 5.2 million over 3 years. Effective date: September 1st. "
            "Nathalie's details: nathalie.dupont@totalenergies.fr, +33 1 47 44 5566. "
            "Legal signatory was General Counsel Marc-Antoine Lefevre (marc.lefevre@totalenergies.fr). "
            "PO number: TTE-2026-PRV-00871. Payment terms: Net 45 to IBAN FR76 3000 4012 3456 7890 1234 567."
        ),
        "expected_tools": ["update_deal"],
        "expected_args": {
            "update_deal": {
                "deal_name": lambda v: "TotalEnergies" in v or "[ORG_" in v,
                "stage": lambda v: v == "closed_won",
                "amount": lambda v: "5.2" in v or "[AMOUNT_" in v,
                "close_date": lambda v: "September" in v or "09" in v,
                "notes": lambda v: "Palantir" in v or "[ORG_" in v or "competitor" in v.lower(),
            },
        },
        "pii_entities": {
            "PERSON": ["Nathalie Dupont", "Marc-Antoine Lefevre"],
            "ORG": ["TotalEnergies", "Palantir"],
            "EMAIL": ["nathalie.dupont@totalenergies.fr", "marc.lefevre@totalenergies.fr"],
            "PHONE": ["+33 1 47 44 5566"],
            "AMOUNT": ["EUR 5.2 million"],
            "ID": ["TTE-2026-PRV-00871"],
            "IBAN": ["FR76 3000 4012 3456 7890 1234 567"],
        },
    },
    {
        "name": "Trade Show Follow-up",
        "instruction": "Create leads for contacts collected at a trade show.",
        "input": (
            "Just got back from CES 2026 in Las Vegas. Two hot leads: "
            "1) Tomoko Ishikawa, Director of Engineering at Samsung Electronics. "
            "She wants our privacy SDK integrated into their SmartThings platform. "
            "Potential deal: $4.1M. Email: tomoko.ishikawa@samsung.com, phone: +82 2 2255 7134. "
            "2) Carlos Méndez-Vega, CTO at MercadoLibre. Looking for PII masking on their "
            "marketplace transactions. Estimated value: $2.7M ARR. "
            "Email: carlos.mendez@mercadolibre.com, phone: +54 11 6842 3390. "
            "Both asked for demos next week. Badge scan IDs: CES-TI-90421 and CES-CM-90422."
        ),
        "expected_tools": ["create_lead"],
        "expected_args": {
            "create_lead": {
                "contact_name": lambda v: "Tomoko Ishikawa" in v or "Carlos" in v or "[PERSON_" in v,
                "company": lambda v: "Samsung" in v or "MercadoLibre" in v or "[ORG_" in v,
                "email": lambda v: "tomoko.ishikawa@samsung.com" in v or "carlos.mendez@mercadolibre.com" in v or "[EMAIL_" in v,
                "phone": lambda v: "+82 2 2255 7134" in v or "+54 11 6842 3390" in v or "[PHONE_" in v,
                "deal_size": lambda v: "4.1M" in v or "2.7M" in v or "[AMOUNT_" in v,
                "source": lambda v: "CES" in v or "trade show" in v.lower() or "[ORG_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Tomoko Ishikawa", "Carlos Méndez-Vega"],
            "ORG": ["Samsung Electronics", "MercadoLibre"],
            "EMAIL": ["tomoko.ishikawa@samsung.com", "carlos.mendez@mercadolibre.com"],
            "PHONE": ["+82 2 2255 7134", "+54 11 6842 3390"],
            "AMOUNT": ["$4.1M", "$2.7M"],
            "ID": ["CES-TI-90421", "CES-CM-90422"],
        },
    },
    {
        "name": "Renewal Negotiation",
        "instruction": "Update the deal with a discount offer and send a retention proposal to prevent churn.",
        "input": (
            "Urgent — Fatima Al-Rashidi at Emirates NBD is threatening to churn. Their contract "
            "renews March 31st, current value AED 8.5 million/year. She says they got an offer from "
            "OneTrust at 30% less. I've been authorized to offer a 20% discount, bringing us to "
            "AED 6.8 million. Move the deal to negotiation. Send the retention proposal to "
            "fatima.alrashidi@emiratesnbd.ae. Her direct line: +971 4 316 2200. "
            "Her manager Khalid bin Saeed (khalid.binsaeed@emiratesnbd.ae) needs to approve. "
            "Account number: ENBD-CORP-2024-07734."
        ),
        "expected_tools": ["update_deal", "send_proposal"],
        "expected_args": {
            "update_deal": {
                "deal_name": lambda v: "Emirates NBD" in v or "[ORG_" in v,
                "stage": lambda v: v == "negotiation",
                "amount": lambda v: "6.8" in v or "[AMOUNT_" in v,
                "close_date": lambda v: "March" in v or "03" in v or "31" in v,
            },
            "send_proposal": {
                "recipient_name": lambda v: "Fatima Al-Rashidi" in v or "[PERSON_" in v,
                "recipient_email": lambda v: "fatima.alrashidi@emiratesnbd.ae" in v or "[EMAIL_" in v,
                "proposal_value": lambda v: "6.8" in v or "[AMOUNT_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Fatima Al-Rashidi", "Khalid bin Saeed"],
            "ORG": ["Emirates NBD", "OneTrust"],
            "EMAIL": ["fatima.alrashidi@emiratesnbd.ae", "khalid.binsaeed@emiratesnbd.ae"],
            "PHONE": ["+971 4 316 2200"],
            "AMOUNT": ["AED 8.5 million", "AED 6.8 million"],
            "ID": ["ENBD-CORP-2024-07734"],
        },
    },
    {
        "name": "Government RFP",
        "instruction": "Create a lead from this government procurement opportunity.",
        "input": (
            "Response to RFP #GS-35F-0119Y from the U.S. General Services Administration. "
            "Primary contact: Dr. Angela Washington, Chief Privacy Officer at the Department of "
            "Veterans Affairs. She's evaluating PII-redaction solutions for veteran health records. "
            "Estimated contract ceiling: $6.3M over 5 years, IDIQ vehicle. "
            "Email: angela.washington@va.gov, phone: +1 202 461 7700. "
            "Contracting Officer: Raymond Begay (raymond.begay@gsa.gov), CAGE code 1PYN7. "
            "Angela's PIV badge number: VA-CPO-00283."
        ),
        "expected_tools": ["create_lead"],
        "expected_args": {
            "create_lead": {
                "contact_name": lambda v: "Angela Washington" in v or "[PERSON_" in v,
                "company": lambda v: "Veterans Affairs" in v or "VA" in v or "[ORG_" in v,
                "email": lambda v: "angela.washington@va.gov" in v or "[EMAIL_" in v,
                "phone": lambda v: "+1 202 461 7700" in v or "[PHONE_" in v,
                "deal_size": lambda v: "6.3M" in v or "6.3" in v or "[AMOUNT_" in v,
                "source": lambda v: "RFP" in v or "GSA" in v or "government" in v.lower() or "[ORG_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Dr. Angela Washington", "Raymond Begay"],
            "ORG": ["U.S. General Services Administration", "Department of Veterans Affairs"],
            "EMAIL": ["angela.washington@va.gov", "raymond.begay@gsa.gov"],
            "PHONE": ["+1 202 461 7700"],
            "AMOUNT": ["$6.3M"],
            "ID": ["GS-35F-0119Y", "1PYN7", "VA-CPO-00283"],
        },
    },
    {
        "name": "Channel Partner Deal",
        "instruction": "Update the deal sourced through our reseller partner.",
        "input": (
            "Wipro has closed qualification on the Siemens Healthineers opportunity. "
            "Our partner contact Rajesh Subramaniam (rajesh.subramaniam@wipro.com, +91 22 5725 8100) "
            "confirmed that Dr. Ingrid Bauer, VP Digital Health at Siemens Healthineers, wants to "
            "proceed. Deal value: EUR 3.9 million for a 2-year license. Move to proposal stage. "
            "Ingrid's email: ingrid.bauer@siemens-healthineers.com. "
            "Wipro's PO reference: WIP-SH-2026-0458. Reseller margin: 18%. "
            "Ingrid's employee ID: SH-DE-84201."
        ),
        "expected_tools": ["update_deal"],
        "expected_args": {
            "update_deal": {
                "deal_name": lambda v: "Siemens" in v or "[ORG_" in v,
                "stage": lambda v: v == "proposal",
                "amount": lambda v: "3.9" in v or "[AMOUNT_" in v,
                "notes": lambda v: "Wipro" in v or "[ORG_" in v or "partner" in v.lower() or "reseller" in v.lower(),
            },
        },
        "pii_entities": {
            "PERSON": ["Rajesh Subramaniam", "Dr. Ingrid Bauer"],
            "ORG": ["Wipro", "Siemens Healthineers"],
            "EMAIL": ["rajesh.subramaniam@wipro.com", "ingrid.bauer@siemens-healthineers.com"],
            "PHONE": ["+91 22 5725 8100"],
            "AMOUNT": ["EUR 3.9 million"],
            "ID": ["WIP-SH-2026-0458", "SH-DE-84201"],
        },
    },
    {
        "name": "Proof of Concept",
        "instruction": "Send a POC proposal to the enterprise prospect.",
        "input": (
            "Ready to send the proof-of-concept proposal to Björn Lindqvist at Spotify. "
            "He's Head of Data Governance and wants a 90-day POC covering their ads platform. "
            "POC value: $450K, with potential full rollout at $5.8M/year. "
            "Email: bjorn.lindqvist@spotify.com, phone: +46 8 5069 3200. "
            "His team lead Sofia Bergström (sofia.bergstrom@spotify.com) should be CC'd. "
            "Billing entity: Spotify AB, VAT SE556703748501. "
            "Björn's Slack handle: @bjorn.lindqvist."
        ),
        "expected_tools": ["send_proposal"],
        "expected_args": {
            "send_proposal": {
                "recipient_name": lambda v: "Björn Lindqvist" in v or "Bjorn" in v or "[PERSON_" in v,
                "recipient_email": lambda v: "bjorn.lindqvist@spotify.com" in v or "[EMAIL_" in v,
                "company": lambda v: "Spotify" in v or "[ORG_" in v,
                "proposal_value": lambda v: "450K" in v or "450" in v or "[AMOUNT_" in v,
                "description": lambda v: "POC" in v or "proof" in v.lower() or "concept" in v.lower() or "90" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Björn Lindqvist", "Sofia Bergström"],
            "ORG": ["Spotify", "Spotify AB"],
            "EMAIL": ["bjorn.lindqvist@spotify.com", "sofia.bergstrom@spotify.com"],
            "PHONE": ["+46 8 5069 3200"],
            "AMOUNT": ["$450K", "$5.8M"],
            "ID": ["SE556703748501"],
            "USERNAME": ["@bjorn.lindqvist"],
        },
    },
    {
        "name": "Territory Handoff",
        "instruction": "Update the deal to reflect the territory transfer to a new sales rep.",
        "input": (
            "Sales rep Oluwaseun Adeyemi is leaving the company on March 15th. Transferring his "
            "LATAM book to new rep Diana Castillo (diana.castillo@ourcompany.com, +1 305 889 4410). "
            "His biggest active deal: Banco Itaú, currently in qualification stage with contact "
            "Renata Oliveira (renata.oliveira@itau.com.br, +55 11 5019 3300). "
            "Deal value: R$9.2 million. Target close: June 30th. "
            "Oluwaseun's employee ID: EMP-0047821. Diana's employee ID: EMP-0052963. "
            "Move the deal to prospecting so Diana can re-qualify. "
            "Add handoff notes about the transition."
        ),
        "expected_tools": ["update_deal"],
        "expected_args": {
            "update_deal": {
                "deal_name": lambda v: "Itaú" in v or "Itau" in v or "Banco" in v or "[ORG_" in v,
                "stage": lambda v: v == "prospecting",
                "amount": lambda v: "9.2" in v or "[AMOUNT_" in v,
                "close_date": lambda v: "June" in v or "06" in v or "30" in v,
                "notes": lambda v: "handoff" in v.lower() or "transfer" in v.lower() or "Diana" in v or "[PERSON_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Oluwaseun Adeyemi", "Diana Castillo", "Renata Oliveira"],
            "ORG": ["Banco Itaú"],
            "EMAIL": ["diana.castillo@ourcompany.com", "renata.oliveira@itau.com.br"],
            "PHONE": ["+1 305 889 4410", "+55 11 5019 3300"],
            "AMOUNT": ["R$9.2 million"],
            "ID": ["EMP-0047821", "EMP-0052963"],
        },
    },
]
