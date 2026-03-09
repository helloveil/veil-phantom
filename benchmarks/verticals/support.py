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
    # ── Scenario 1: Billing Dispute ──────────────────────────────────────
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
        "pii_entities": {
            "PERSON": ["Grace Nkomo"],
            "AMOUNT": ["$299.99"],
            "EMAIL": ["grace.nkomo@gmail.com"],
            "PHONE": ["+27 82 991 3345"],
            "CREDIT_CARD_FRAGMENT": ["7823"],
        },
        "expected_args": {
            "create_ticket": {
                "customer_name": lambda v: "Grace Nkomo" in v or "[PERSON_" in v,
                "customer_email": lambda v: "grace.nkomo@gmail.com" in v or "[EMAIL_" in v,
                "subject": lambda v: len(v) > 0,
                "description": lambda v: len(v) > 0,
            },
            "process_refund": {
                "customer_name": lambda v: "Grace Nkomo" in v or "[PERSON_" in v,
                "amount": lambda v: "299.99" in v or "[AMOUNT_" in v,
                "reason": lambda v: len(v) > 0,
            },
        },
    },
    # ── Scenario 2: Service Outage Escalation ────────────────────────────
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
        "pii_entities": {
            "ORG": ["Absa Group"],
            "PERSON": ["Mohammed Ismail"],
            "AMOUNT": ["R12M"],
            "PHONE": ["+27 11 350 4000"],
            "EMAIL": ["m.ismail@absa.co.za"],
        },
        "expected_args": {
            "create_ticket": {
                "customer_name": lambda v: "Mohammed Ismail" in v or "Absa Group" in v or "[PERSON_" in v or "[ORG_" in v,
                "subject": lambda v: len(v) > 0,
                "description": lambda v: len(v) > 0,
                "priority": lambda v: v in ("high", "critical"),
            },
            "escalate_ticket": {
                "escalate_to": lambda v: len(v) > 0,
                "reason": lambda v: len(v) > 0,
            },
        },
    },
    # ── Scenario 3: Product Return ───────────────────────────────────────
    {
        "name": "Product Return",
        "instruction": "Process this return and refund request.",
        "input": (
            "Anele Zulu wants to return 3 units of the Pro Plan license purchased on Feb 28th. "
            "Order #ORD-2026-51234. Total refund: $897. Reason: switching to competitor. "
            "Refund to bank account FNB 6245 7890 123. Email: anele@techstartup.co.za."
        ),
        "expected_tools": ["process_refund"],
        "pii_entities": {
            "PERSON": ["Anele Zulu"],
            "AMOUNT": ["$897"],
            "BANK_ACCOUNT": ["6245 7890 123"],
            "EMAIL": ["anele@techstartup.co.za"],
        },
        "expected_args": {
            "process_refund": {
                "customer_name": lambda v: "Anele Zulu" in v or "[PERSON_" in v,
                "amount": lambda v: "897" in v or "[AMOUNT_" in v,
                "reason": lambda v: len(v) > 0,
            },
        },
    },
    # ── Scenario 4: Account Compromise ───────────────────────────────────
    {
        "name": "Account Compromise",
        "instruction": "Create a critical ticket and escalate to the security team for this compromised account report.",
        "input": (
            "Fatima Al-Rashidi is reporting unauthorized access to her account. She noticed "
            "three transactions she didn't make totalling $1,247.50 on March 7th. "
            "The suspicious login came from IP 185.220.101.42 using a Windows device with "
            "user-agent 'Mozilla/5.0 (Windows NT 10.0; rv:102.0)' — she only uses macOS. "
            "Her account ID is ACC-8827341. She last logged in legitimately from IP 41.13.252.87 "
            "(Cape Town). Email: fatima.rashidi@outlook.com. Phone: +971 50 884 2219. "
            "She has 2FA enabled but suspects a SIM-swap attack on her number +971 55 300 1178."
        ),
        "expected_tools": ["create_ticket", "escalate_ticket"],
        "pii_entities": {
            "PERSON": ["Fatima Al-Rashidi"],
            "AMOUNT": ["$1,247.50"],
            "IP_ADDRESS": ["185.220.101.42", "41.13.252.87"],
            "ACCOUNT_ID": ["ACC-8827341"],
            "EMAIL": ["fatima.rashidi@outlook.com"],
            "PHONE": ["+971 50 884 2219", "+971 55 300 1178"],
        },
        "expected_args": {
            "create_ticket": {
                "customer_name": lambda v: "Fatima Al-Rashidi" in v or "[PERSON_" in v,
                "customer_email": lambda v: "fatima.rashidi@outlook.com" in v or "[EMAIL_" in v,
                "subject": lambda v: len(v) > 0,
                "description": lambda v: len(v) > 0,
                "priority": lambda v: v in ("high", "critical"),
            },
            "escalate_ticket": {
                "escalate_to": lambda v: len(v) > 0,
                "reason": lambda v: len(v) > 0,
            },
        },
    },
    # ── Scenario 5: Subscription Cancellation ────────────────────────────
    {
        "name": "Subscription Cancellation",
        "instruction": "Create a ticket for this cancellation request. Attempt retention by processing a partial refund as goodwill.",
        "input": (
            "Long-time customer Priya Nair (5 years) wants to cancel her Business Plus subscription "
            "effective immediately. Monthly charge: $149/month, annual contract value $1,788. "
            "Order #ORD-2024-30076. She says the reporting features don't meet her needs anymore. "
            "She's already migrating her team of 12 to a competitor. "
            "Account email: priya.nair@blueocean.in. Personal email: priyanair88@gmail.com. "
            "Phone: +91 98765 43210. Company: Blue Ocean Analytics Pvt. Ltd. "
            "Offer a one-month goodwill refund of $149 to her original payment method."
        ),
        "expected_tools": ["create_ticket", "process_refund"],
        "pii_entities": {
            "PERSON": ["Priya Nair"],
            "ORG": ["Blue Ocean Analytics Pvt. Ltd."],
            "AMOUNT": ["$149", "$1,788"],
            "EMAIL": ["priya.nair@blueocean.in", "priyanair88@gmail.com"],
            "PHONE": ["+91 98765 43210"],
            "ORDER_ID": ["ORD-2024-30076"],
        },
        "expected_args": {
            "create_ticket": {
                "customer_name": lambda v: "Priya Nair" in v or "[PERSON_" in v,
                "customer_email": lambda v: "priya.nair@blueocean.in" in v or "priyanair88@gmail.com" in v or "[EMAIL_" in v,
                "subject": lambda v: len(v) > 0,
                "description": lambda v: len(v) > 0,
            },
            "process_refund": {
                "customer_name": lambda v: "Priya Nair" in v or "[PERSON_" in v,
                "amount": lambda v: "149" in v or "[AMOUNT_" in v,
                "reason": lambda v: len(v) > 0,
            },
        },
    },
    # ── Scenario 6: Data Export Request ──────────────────────────────────
    {
        "name": "Data Export Request",
        "instruction": "Create a ticket for this data subject access request and escalate to the data protection officer.",
        "input": (
            "Thabiso Molefe is exercising his right under POPIA (and GDPR, as he also has an EU "
            "account) to request a full export of all personal data held about him. "
            "SA ID number: 9201015800086. Passport: M00482190 (South Africa). "
            "Account email: thabiso.molefe@juridica.co.za. Secondary: t.molefe@proton.me. "
            "Phone: +27 63 441 8823. Residential address: 14 Bree Street, Cape Town, 8001. "
            "He requests the data be delivered in machine-readable JSON format within 30 days. "
            "Company: Juridica Legal Consulting. Customer since 2019, account #CUS-2019-00482. "
            "Escalate to the Data Protection Officer for compliance review."
        ),
        "expected_tools": ["create_ticket", "escalate_ticket"],
        "pii_entities": {
            "PERSON": ["Thabiso Molefe"],
            "NATIONAL_ID": ["9201015800086"],
            "PASSPORT": ["M00482190"],
            "EMAIL": ["thabiso.molefe@juridica.co.za", "t.molefe@proton.me"],
            "PHONE": ["+27 63 441 8823"],
            "ADDRESS": ["14 Bree Street, Cape Town, 8001"],
            "ORG": ["Juridica Legal Consulting"],
            "ACCOUNT_ID": ["CUS-2019-00482"],
        },
        "expected_args": {
            "create_ticket": {
                "customer_name": lambda v: "Thabiso Molefe" in v or "[PERSON_" in v,
                "customer_email": lambda v: "thabiso.molefe@juridica.co.za" in v or "t.molefe@proton.me" in v or "[EMAIL_" in v,
                "subject": lambda v: len(v) > 0,
                "description": lambda v: len(v) > 0,
                "priority": lambda v: v in ("high", "critical"),
            },
            "escalate_ticket": {
                "escalate_to": lambda v: "data protection" in v.lower() or "dpo" in v.lower() or "privacy" in v.lower() or "compliance" in v.lower(),
                "reason": lambda v: len(v) > 0,
            },
        },
    },
    # ── Scenario 7: Integration Failure ────────────────────────────────
    {
        "name": "Integration Failure",
        "instruction": "Create a critical ticket and escalate to the platform engineering lead for this enterprise API integration failure.",
        "input": (
            "Enterprise customer Meridian Logistics (contact: Henrik Johansson, VP Engineering) "
            "reports their REST API integration has been returning 502 errors since 09:15 UTC. "
            "Their SLA guarantees a 15-minute response time for P1 incidents — we are now at 47 minutes. "
            "This is blocking their real-time shipment tracking for 12,000+ daily deliveries. "
            "Contract value: €2.4M/year. Account ID: ENT-4420-MRD. "
            "Henrik's email: h.johansson@meridianlogistics.eu. Phone: +46 70 839 2214. "
            "Escalate to the Platform Engineering Lead immediately before SLA penalties kick in."
        ),
        "expected_tools": ["create_ticket", "escalate_ticket"],
        "pii_entities": {
            "ORG": ["Meridian Logistics"],
            "PERSON": ["Henrik Johansson"],
            "AMOUNT": ["€2.4M"],
            "ACCOUNT_ID": ["ENT-4420-MRD"],
            "EMAIL": ["h.johansson@meridianlogistics.eu"],
            "PHONE": ["+46 70 839 2214"],
        },
        "expected_args": {
            "create_ticket": {
                "customer_name": lambda v: "Henrik Johansson" in v or "Meridian Logistics" in v or "[PERSON_" in v or "[ORG_" in v,
                "subject": lambda v: len(v) > 0,
                "description": lambda v: len(v) > 0,
                "priority": lambda v: v in ("high", "critical"),
            },
            "escalate_ticket": {
                "escalate_to": lambda v: len(v) > 0,
                "reason": lambda v: "SLA" in v.upper() or "integration" in v.lower() or "API" in v or "502" in v or len(v) > 0,
            },
        },
    },
    # ── Scenario 8: Bulk Refund ────────────────────────────────────────
    {
        "name": "Bulk Refund",
        "instruction": "Process a bulk refund for this service outage affecting multiple charges.",
        "input": (
            "Due to the 6-hour platform outage on March 4th, customer Luciana Ferreira is owed "
            "a refund of $3,450.00 covering three separate failed transaction batches. "
            "Order references: ORD-2026-78101, ORD-2026-78102, ORD-2026-78103. "
            "Her company, SolBright Energy Corp, processes solar panel installations through our platform. "
            "Account email: l.ferreira@solbrightenergy.com.br. Phone: +55 11 97654 3210. "
            "Account ID: ACC-5593201. Refund to original Visa card ending 4491. "
            "Reason: service outage SLA credit per incident INC-20260304-001."
        ),
        "expected_tools": ["process_refund"],
        "pii_entities": {
            "PERSON": ["Luciana Ferreira"],
            "ORG": ["SolBright Energy Corp"],
            "AMOUNT": ["$3,450.00"],
            "ORDER_ID": ["ORD-2026-78101", "ORD-2026-78102", "ORD-2026-78103"],
            "EMAIL": ["l.ferreira@solbrightenergy.com.br"],
            "PHONE": ["+55 11 97654 3210"],
            "ACCOUNT_ID": ["ACC-5593201"],
            "CREDIT_CARD_FRAGMENT": ["4491"],
        },
        "expected_args": {
            "process_refund": {
                "customer_name": lambda v: "Luciana Ferreira" in v or "[PERSON_" in v,
                "amount": lambda v: "3,450" in v or "3450" in v or "[AMOUNT_" in v,
                "reason": lambda v: "outage" in v.lower() or "SLA" in v or len(v) > 0,
            },
        },
    },
    # ── Scenario 9: Feature Request ────────────────────────────────────
    {
        "name": "Feature Request",
        "instruction": "Create a ticket to track this enterprise feature request from a key customer.",
        "input": (
            "Kenji Watanabe, Head of Data at NovaCrest Financial, is requesting a custom SSO "
            "integration with their Okta identity provider. They need SAML 2.0 support with "
            "attribute mapping for role-based access control across 340 users. "
            "NovaCrest's annual contract is $480,000 and renewal is in 60 days — this feature "
            "is a blocker for renewal. Account ID: ENT-7891-NVC. "
            "Email: k.watanabe@novacrestfinancial.com. Phone: +81 3 6205 4488. "
            "He's provided a detailed requirements document at their shared drive. "
            "Priority: high — renewal at risk without this."
        ),
        "expected_tools": ["create_ticket"],
        "pii_entities": {
            "PERSON": ["Kenji Watanabe"],
            "ORG": ["NovaCrest Financial"],
            "AMOUNT": ["$480,000"],
            "ACCOUNT_ID": ["ENT-7891-NVC"],
            "EMAIL": ["k.watanabe@novacrestfinancial.com"],
            "PHONE": ["+81 3 6205 4488"],
        },
        "expected_args": {
            "create_ticket": {
                "customer_name": lambda v: "Kenji Watanabe" in v or "NovaCrest" in v or "[PERSON_" in v or "[ORG_" in v,
                "customer_email": lambda v: "k.watanabe@novacrestfinancial.com" in v or "[EMAIL_" in v,
                "subject": lambda v: "SSO" in v.upper() or "feature" in v.lower() or "integration" in v.lower() or len(v) > 0,
                "description": lambda v: len(v) > 0,
                "priority": lambda v: v in ("high", "critical"),
                "category": lambda v: len(v) > 0,
            },
        },
    },
    # ── Scenario 10: Security Vulnerability Report ─────────────────────
    {
        "name": "Security Vulnerability Report",
        "instruction": "Create a critical ticket and immediately escalate to the security response team for this vulnerability report.",
        "input": (
            "Security researcher Daria Volkov has reported a stored XSS vulnerability in the "
            "customer dashboard's comment field. She demonstrated that injected JavaScript can "
            "exfiltrate session tokens via a crafted payload. Affected endpoint: "
            "/api/v2/comments. CVSS score: 8.1 (High). She found it through your bug bounty "
            "program (HackerOne handle: d_volkov_sec). "
            "Email: daria.volkov@securemail.ch. Phone: +41 44 520 8837. "
            "She requests acknowledgment within 24 hours per your responsible disclosure policy. "
            "Account ID: BB-2026-0047. Escalate to the Security Response Team lead immediately."
        ),
        "expected_tools": ["create_ticket", "escalate_ticket"],
        "pii_entities": {
            "PERSON": ["Daria Volkov"],
            "EMAIL": ["daria.volkov@securemail.ch"],
            "PHONE": ["+41 44 520 8837"],
            "ACCOUNT_ID": ["BB-2026-0047"],
        },
        "expected_args": {
            "create_ticket": {
                "customer_name": lambda v: "Daria Volkov" in v or "[PERSON_" in v,
                "customer_email": lambda v: "daria.volkov@securemail.ch" in v or "[EMAIL_" in v,
                "subject": lambda v: "XSS" in v or "security" in v.lower() or "vulnerability" in v.lower() or len(v) > 0,
                "description": lambda v: len(v) > 0,
                "priority": lambda v: v in ("high", "critical"),
            },
            "escalate_ticket": {
                "escalate_to": lambda v: "security" in v.lower() or "ciso" in v.lower() or len(v) > 0,
                "reason": lambda v: "vulnerability" in v.lower() or "XSS" in v or "security" in v.lower() or len(v) > 0,
            },
        },
    },
    # ── Scenario 11: Warranty Claim ────────────────────────────────────
    {
        "name": "Warranty Claim",
        "instruction": "Create a ticket for this warranty claim and process the refund for the defective hardware.",
        "input": (
            "Customer Amara Okafor purchased a ProConnect Gateway device (SKU: PCG-5000X) on "
            "December 10th, 2025. The device developed a persistent overheating issue after 11 weeks, "
            "well within the 2-year warranty period. Serial number: SN-PCG-2025-88431. "
            "Order #ORD-2025-99217. Original purchase price: $749.95. "
            "She has already shipped the defective unit back (return tracking: RTN-4478822). "
            "Email: amara.okafor@cloudnova.ng. Phone: +234 803 552 6617. "
            "Process a full refund of $749.95 to her original payment method while a replacement is arranged."
        ),
        "expected_tools": ["create_ticket", "process_refund"],
        "pii_entities": {
            "PERSON": ["Amara Okafor"],
            "AMOUNT": ["$749.95"],
            "ORDER_ID": ["ORD-2025-99217"],
            "EMAIL": ["amara.okafor@cloudnova.ng"],
            "PHONE": ["+234 803 552 6617"],
        },
        "expected_args": {
            "create_ticket": {
                "customer_name": lambda v: "Amara Okafor" in v or "[PERSON_" in v,
                "customer_email": lambda v: "amara.okafor@cloudnova.ng" in v or "[EMAIL_" in v,
                "subject": lambda v: "warranty" in v.lower() or "defective" in v.lower() or "hardware" in v.lower() or len(v) > 0,
                "description": lambda v: len(v) > 0,
            },
            "process_refund": {
                "customer_name": lambda v: "Amara Okafor" in v or "[PERSON_" in v,
                "amount": lambda v: "749.95" in v or "[AMOUNT_" in v,
                "reason": lambda v: "warranty" in v.lower() or "defective" in v.lower() or len(v) > 0,
            },
        },
    },
    # ── Scenario 12: Billing Migration ─────────────────────────────────
    {
        "name": "Billing Migration",
        "instruction": "Process the prorated refund credit for this customer migrating to a new billing plan.",
        "input": (
            "Customer Rafael Mendes is migrating from the Enterprise Annual plan ($18,000/year) "
            "to the Enterprise Monthly plan ($1,800/month) effective immediately. "
            "He has 4 months and 12 days remaining on his annual contract. "
            "Prorated credit due: $6,600.00 covering the unused portion of his annual plan. "
            "Company: DataStream Analytics LLC. Account ID: ENT-3301-DSA. "
            "Order #ORD-2025-61450. Email: r.mendes@datastreamanalytics.io. "
            "Phone: +1 512 884 7730. Refund the prorated amount to company bank account on file."
        ),
        "expected_tools": ["process_refund"],
        "pii_entities": {
            "PERSON": ["Rafael Mendes"],
            "ORG": ["DataStream Analytics LLC"],
            "AMOUNT": ["$18,000", "$1,800", "$6,600.00"],
            "ACCOUNT_ID": ["ENT-3301-DSA"],
            "ORDER_ID": ["ORD-2025-61450"],
            "EMAIL": ["r.mendes@datastreamanalytics.io"],
            "PHONE": ["+1 512 884 7730"],
        },
        "expected_args": {
            "process_refund": {
                "customer_name": lambda v: "Rafael Mendes" in v or "[PERSON_" in v,
                "amount": lambda v: "6,600" in v or "6600" in v or "[AMOUNT_" in v,
                "reason": lambda v: "migration" in v.lower() or "prorat" in v.lower() or "plan" in v.lower() or len(v) > 0,
            },
        },
    },
]
