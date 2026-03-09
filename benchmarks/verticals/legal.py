"""Legal vertical — contract review, compliance, case management."""

import re

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


def _token_pattern(label: str) -> re.Pattern:
    """Return a compiled regex that matches VeilPhantom tokens like [PERSON_1]."""
    return re.compile(rf"\[{label}_\d+\]")


def _pii_or_token(value: str, pii: str, token_label: str) -> bool:
    """Return True if *value* contains the raw PII string OR a VeilPhantom token."""
    return pii in value or bool(_token_pattern(token_label).search(value))


SCENARIOS = [
    # ── 1. New Litigation (existing) ────────────────────────────────────
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
        "pii_entities": {
            "PERSON": ["Sipho Nkosi", "Adv. Rebecca van der Merwe"],
            "ORG": ["GlobalTech SA", "Norton Rose Fulbright"],
            "GOVID": ["890412 5123 087"],
            "AMOUNT": ["R85,000"],
            "CASE_ID": ["LC-2026-0312"],
        },
        "expected_args": {
            "create_case": {
                "client_name": lambda v: _pii_or_token(v, "Sipho Nkosi", "PERSON"),
                "opposing_party": lambda v: _pii_or_token(v, "GlobalTech SA", "ORG"),
                "assigned_attorney": lambda v: _pii_or_token(v, "Adv. Rebecca van der Merwe", "PERSON"),
                "case_type": lambda v: "wrongful" in v.lower() or "dismissal" in v.lower(),
            },
        },
    },
    # ── 2. NDA Clause (existing) ────────────────────────────────────────
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
        "pii_entities": {
            "PERSON": ["Nakai Williams", "Park Joon-ho"],
            "ORG": ["Veil Technologies", "Samsung Electronics"],
            "EMAIL": ["nakai@helloveil.com", "joonho.park@samsung.com"],
        },
        "expected_args": {
            "draft_contract_clause": {
                "clause_type": lambda v: "nda" in v.lower() or "non-disclosure" in v.lower() or "confidential" in v.lower(),
                "parties": lambda v: (
                    (_pii_or_token(str(v), "Veil Technologies", "ORG"))
                    and (_pii_or_token(str(v), "Samsung Electronics", "ORG"))
                ),
                "terms": lambda v: "3 year" in v.lower() or "three year" in v.lower() or bool(_token_pattern("DATE").search(v)),
            },
        },
    },
    # ── 3. POPIA Compliance (existing) ──────────────────────────────────
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
        "pii_entities": {
            "PERSON": ["James Fletcher"],
            "ORG": ["MediCare Holdings"],
            "EMAIL": ["j.fletcher@medicare.co.za"],
            "PHONE": ["+27 11 555 8901"],
        },
        "expected_args": {
            "file_compliance_report": {
                "company": lambda v: _pii_or_token(v, "MediCare Holdings", "ORG"),
                "regulation": lambda v: "popia" in v.lower() or "protection of personal information" in v.lower(),
                "findings": lambda v: (
                    ("unencrypted" in v.lower() or "breach" in v.lower() or "s3" in v.lower())
                    and (_pii_or_token(v, "James Fletcher", "PERSON") or bool(_token_pattern("PERSON").search(v)))
                ),
            },
        },
    },
    # ── 4. Patent Filing (new) ──────────────────────────────────────────
    {
        "name": "Patent Filing",
        "instruction": "Create a case to track this patent application filing.",
        "input": (
            "File a provisional patent for Dr. Amara Osei (ID: 850617 2234 081) of NeuroWave "
            "Labs (Pty) Ltd. The invention is a non-invasive brain-computer interface using "
            "graphene nano-sensors — patent application ZA-2026-PAT-04871. Amara's co-inventor "
            "is Dr. Kenji Watanabe (kenji.watanabe@neurowave.co.za, +27 21 443 6712). "
            "Filing fee: R12,500. Deadline to file with CIPC: April 15th 2026. "
            "Attorney on record: Thandi Molefe, Adams & Adams, thandi.molefe@adamsadams.com."
        ),
        "expected_tools": ["create_case"],
        "pii_entities": {
            "PERSON": ["Dr. Amara Osei", "Dr. Kenji Watanabe", "Thandi Molefe"],
            "ORG": ["NeuroWave Labs", "Adams & Adams"],
            "GOVID": ["850617 2234 081"],
            "EMAIL": ["kenji.watanabe@neurowave.co.za", "thandi.molefe@adamsadams.com"],
            "PHONE": ["+27 21 443 6712"],
            "AMOUNT": ["R12,500"],
            "CASE_ID": ["ZA-2026-PAT-04871"],
        },
        "expected_args": {
            "create_case": {
                "client_name": lambda v: _pii_or_token(v, "Dr. Amara Osei", "PERSON"),
                "case_type": lambda v: "patent" in v.lower(),
                "assigned_attorney": lambda v: _pii_or_token(v, "Thandi Molefe", "PERSON"),
                "filing_deadline": lambda v: "april" in v.lower() or "2026-04" in v or bool(_token_pattern("DATE").search(v)),
            },
        },
    },
    # ── 5. Merger Review (new) ──────────────────────────────────────────
    {
        "name": "Merger Review",
        "instruction": "File a compliance report for this proposed merger review.",
        "input": (
            "The Competition Commission of South Africa is reviewing the proposed acquisition "
            "of SilverBridge Payments by Naspers Fintech division. Transaction value: R2.4 billion. "
            "SilverBridge CEO Lindiwe Dlamini (lindiwe@silverbridge.co.za, +27 12 998 3340) "
            "and Naspers Fintech head Ravi Chetty (ravi.chetty@naspers.com) submitted the merger "
            "notification on February 20, 2026. The combined entity would control 38% of the "
            "digital payments market. Regulatory counsel: Adv. Pieter Botha, ENSafrica, ID 760923 5098 062. "
            "Deadline for Phase 1 determination: May 1st 2026."
        ),
        "expected_tools": ["file_compliance_report"],
        "pii_entities": {
            "PERSON": ["Lindiwe Dlamini", "Ravi Chetty", "Adv. Pieter Botha"],
            "ORG": ["SilverBridge Payments", "Naspers Fintech", "ENSafrica", "Competition Commission of South Africa"],
            "EMAIL": ["lindiwe@silverbridge.co.za", "ravi.chetty@naspers.com"],
            "PHONE": ["+27 12 998 3340"],
            "GOVID": ["760923 5098 062"],
            "AMOUNT": ["R2.4 billion"],
        },
        "expected_args": {
            "file_compliance_report": {
                "company": lambda v: (
                    _pii_or_token(v, "SilverBridge Payments", "ORG")
                    or _pii_or_token(v, "Naspers Fintech", "ORG")
                ),
                "regulation": lambda v: (
                    "competition" in v.lower() or "merger" in v.lower() or "antitrust" in v.lower()
                ),
                "findings": lambda v: (
                    ("acquisition" in v.lower() or "merger" in v.lower() or "38%" in v)
                    and (_pii_or_token(v, "R2.4 billion", "AMOUNT") or bool(_token_pattern("AMOUNT").search(v)))
                ),
                "risk_level": lambda v: v in ("medium", "high", "critical"),
            },
        },
    },
    # ── 6. Settlement Agreement (new) ───────────────────────────────────
    {
        "name": "Settlement Agreement",
        "instruction": "Draft a settlement clause based on these negotiation terms.",
        "input": (
            "Settlement reached between Zanele Mbeki (zanele.mbeki@gmail.com, ID 910305 0187 045) "
            "and her former employer Deloitte Africa. Zanele was represented by Adv. Farouk Essop "
            "(farouk@essoplaw.co.za, +27 31 267 4455). Terms: Deloitte will pay R1,250,000 in "
            "three instalments — R500,000 on signing, R375,000 after 90 days, and R375,000 after "
            "180 days. Zanele agrees to a 2-year non-compete and full non-disclosure. "
            "Deloitte contact: HR Director Priya Naidoo, priya.naidoo@deloitte.co.za. "
            "Settlement reference: SET-2026-JHB-0098."
        ),
        "expected_tools": ["draft_contract_clause"],
        "pii_entities": {
            "PERSON": ["Zanele Mbeki", "Adv. Farouk Essop", "Priya Naidoo"],
            "ORG": ["Deloitte Africa"],
            "EMAIL": ["zanele.mbeki@gmail.com", "farouk@essoplaw.co.za", "priya.naidoo@deloitte.co.za"],
            "PHONE": ["+27 31 267 4455"],
            "GOVID": ["910305 0187 045"],
            "AMOUNT": ["R1,250,000", "R500,000", "R375,000"],
            "CASE_ID": ["SET-2026-JHB-0098"],
        },
        "expected_args": {
            "draft_contract_clause": {
                "clause_type": lambda v: "settlement" in v.lower(),
                "parties": lambda v: (
                    (_pii_or_token(str(v), "Zanele Mbeki", "PERSON"))
                    and (_pii_or_token(str(v), "Deloitte Africa", "ORG"))
                ),
                "terms": lambda v: (
                    (_pii_or_token(v, "R1,250,000", "AMOUNT") or bool(_token_pattern("AMOUNT").search(v)))
                    and ("instal" in v.lower() or "payment" in v.lower() or "signing" in v.lower())
                ),
            },
        },
    },
    # ── 7. IP Infringement ────────────────────────────────────────────
    {
        "name": "IP Infringement",
        "instruction": "Create a case for this intellectual property dispute.",
        "input": (
            "LuminArc Design Studio is filing a copyright and trademark infringement suit "
            "against PixelForge Inc. LuminArc's lead designer, Chiara Bianchi (chiara.bianchi@luminarc.it, "
            "ID 820714 3345 092), discovered that PixelForge copied their patented UI framework "
            "'ArcFlow' and replicated the LuminArc logo across 14 product pages. "
            "Case reference: IP-2026-CPT-0741. Damages sought: R3,800,000 plus injunctive relief. "
            "LuminArc's attorney is Adv. Nkululeko Zulu (nkululeko@zuluip.co.za, +27 21 874 3390) "
            "of Zulu IP Chambers. Filing with the Western Cape High Court by March 28th 2026."
        ),
        "expected_tools": ["create_case"],
        "pii_entities": {
            "PERSON": ["Chiara Bianchi", "Adv. Nkululeko Zulu"],
            "ORG": ["LuminArc Design Studio", "PixelForge Inc", "Zulu IP Chambers"],
            "EMAIL": ["chiara.bianchi@luminarc.it", "nkululeko@zuluip.co.za"],
            "PHONE": ["+27 21 874 3390"],
            "GOVID": ["820714 3345 092"],
            "AMOUNT": ["R3,800,000"],
            "CASE_ID": ["IP-2026-CPT-0741"],
        },
        "expected_args": {
            "create_case": {
                "client_name": lambda v: _pii_or_token(v, "LuminArc Design Studio", "ORG"),
                "opposing_party": lambda v: _pii_or_token(v, "PixelForge Inc", "ORG"),
                "case_type": lambda v: (
                    "infringement" in v.lower()
                    or "copyright" in v.lower()
                    or "trademark" in v.lower()
                    or "intellectual property" in v.lower()
                    or "ip" in v.lower()
                ),
                "assigned_attorney": lambda v: _pii_or_token(v, "Adv. Nkululeko Zulu", "PERSON"),
                "court": lambda v: "western cape" in v.lower() or "high court" in v.lower() or bool(_token_pattern("ORG").search(v)),
            },
        },
    },
    # ── 8. Employment Contract ────────────────────────────────────────
    {
        "name": "Employment Contract",
        "instruction": "Draft an employment agreement clause based on this offer.",
        "input": (
            "Draft an employment contract between Momentum Health Solutions and Dr. Fatima "
            "Al-Rashidi (fatima.alrashidi@gmail.com, ID 880219 5567 083, +27 83 221 6745). "
            "Role: Chief Data Officer. Annual base salary: R2,150,000 with a 15% performance "
            "bonus. Stock options: 25,000 shares vesting over 4 years. Start date: May 1st 2026. "
            "Reporting to CEO Marcus van Wyk (marcus.vanwyk@momentum.co.za). "
            "Non-compete: 18 months post-departure within healthcare analytics. "
            "Contract drafted by Webber Wentzel, attorney on file: Adv. Samantha Reddy, "
            "samantha.reddy@webberwentzel.com."
        ),
        "expected_tools": ["draft_contract_clause"],
        "pii_entities": {
            "PERSON": ["Dr. Fatima Al-Rashidi", "Marcus van Wyk", "Adv. Samantha Reddy"],
            "ORG": ["Momentum Health Solutions", "Webber Wentzel"],
            "EMAIL": ["fatima.alrashidi@gmail.com", "marcus.vanwyk@momentum.co.za", "samantha.reddy@webberwentzel.com"],
            "PHONE": ["+27 83 221 6745"],
            "GOVID": ["880219 5567 083"],
            "AMOUNT": ["R2,150,000"],
        },
        "expected_args": {
            "draft_contract_clause": {
                "clause_type": lambda v: "employment" in v.lower() or "offer" in v.lower() or "hiring" in v.lower(),
                "parties": lambda v: (
                    (_pii_or_token(str(v), "Momentum Health Solutions", "ORG"))
                    and (_pii_or_token(str(v), "Dr. Fatima Al-Rashidi", "PERSON"))
                ),
                "terms": lambda v: (
                    (_pii_or_token(v, "R2,150,000", "AMOUNT") or bool(_token_pattern("AMOUNT").search(v)))
                    and ("salary" in v.lower() or "compensation" in v.lower() or "stock" in v.lower() or "bonus" in v.lower())
                ),
            },
        },
    },
    # ── 9. GDPR Audit ─────────────────────────────────────────────────
    {
        "name": "GDPR Audit",
        "instruction": "File a compliance report based on this GDPR audit finding.",
        "input": (
            "An internal audit of EuroVault GmbH (Berlin, Germany) revealed GDPR Article 32 "
            "violations: personally identifiable data of 47,000 EU citizens was processed without "
            "adequate encryption or pseudonymisation. Data Protection Officer Henrik Johansson "
            "(henrik.johansson@eurovault.de, +49 30 8834 2210) confirmed that customer names, "
            "addresses, and IBAN numbers (e.g. DE89 3704 0044 0532 0130 00) were transmitted in "
            "plaintext via an unpatched API endpoint. The breach window is estimated between "
            "December 10, 2025 and February 2, 2026. The lead EU privacy counsel is Adv. Sofia "
            "Papadopoulos (sofia.p@gdprcounsel.eu, Greek Bar No. 44219). Notification to the "
            "Berlin Commissioner for Data Protection is required within 72 hours. Estimated fine "
            "exposure: EUR 4,200,000."
        ),
        "expected_tools": ["file_compliance_report"],
        "pii_entities": {
            "PERSON": ["Henrik Johansson", "Adv. Sofia Papadopoulos"],
            "ORG": ["EuroVault GmbH"],
            "EMAIL": ["henrik.johansson@eurovault.de", "sofia.p@gdprcounsel.eu"],
            "PHONE": ["+49 30 8834 2210"],
            "GOVID": ["DE89 3704 0044 0532 0130 00", "44219"],
            "AMOUNT": ["EUR 4,200,000"],
        },
        "expected_args": {
            "file_compliance_report": {
                "company": lambda v: _pii_or_token(v, "EuroVault GmbH", "ORG"),
                "regulation": lambda v: "gdpr" in v.lower() or "general data protection" in v.lower(),
                "findings": lambda v: (
                    ("encryption" in v.lower() or "plaintext" in v.lower() or "unpatched" in v.lower())
                    and ("47,000" in v or "47000" in v or "citizens" in v.lower() or bool(_token_pattern("PERSON").search(v)))
                ),
                "risk_level": lambda v: v in ("high", "critical"),
            },
        },
    },
    # ── 10. Divorce Settlement ────────────────────────────────────────
    {
        "name": "Divorce Settlement",
        "instruction": "Draft a property division clause for this divorce settlement.",
        "input": (
            "Divorce settlement between Ayanda Khumalo (ID 790806 0298 064, ayanda.k@webmail.co.za, "
            "+27 72 310 8845) and Thabo Khumalo (ID 781123 5410 089, thabo.khumalo@outlook.com). "
            "Married in community of property on June 15, 2008. Joint estate valued at R8,750,000, "
            "comprising: primary residence in Sandton (R4,200,000), holiday home in Ballito "
            "(R2,100,000), investment portfolio at Allan Gray (R1,650,000), and vehicles (R800,000). "
            "Ayanda retains primary residence and vehicles; Thabo retains holiday home and "
            "investments plus a R425,000 equalisation payment from Ayanda. Child maintenance for "
            "two minors: R18,500/month each. Attorney for Ayanda: Nombulelo Sithole, Bowmans, "
            "nombulelo.sithole@bowmanslaw.com. Attorney for Thabo: Grant Peterson, "
            "grant.peterson@cdhlegal.com."
        ),
        "expected_tools": ["draft_contract_clause"],
        "pii_entities": {
            "PERSON": ["Ayanda Khumalo", "Thabo Khumalo", "Nombulelo Sithole", "Grant Peterson"],
            "ORG": ["Allan Gray", "Bowmans"],
            "EMAIL": ["ayanda.k@webmail.co.za", "thabo.khumalo@outlook.com", "nombulelo.sithole@bowmanslaw.com", "grant.peterson@cdhlegal.com"],
            "PHONE": ["+27 72 310 8845"],
            "GOVID": ["790806 0298 064", "781123 5410 089"],
            "AMOUNT": ["R8,750,000", "R4,200,000", "R2,100,000", "R1,650,000", "R800,000", "R425,000", "R18,500"],
        },
        "expected_args": {
            "draft_contract_clause": {
                "clause_type": lambda v: (
                    "divorce" in v.lower()
                    or "settlement" in v.lower()
                    or "property division" in v.lower()
                    or "matrimonial" in v.lower()
                ),
                "parties": lambda v: (
                    (_pii_or_token(str(v), "Ayanda Khumalo", "PERSON"))
                    and (_pii_or_token(str(v), "Thabo Khumalo", "PERSON"))
                ),
                "terms": lambda v: (
                    (_pii_or_token(v, "R8,750,000", "AMOUNT") or bool(_token_pattern("AMOUNT").search(v)))
                    and ("residence" in v.lower() or "property" in v.lower() or "vehicle" in v.lower())
                ),
            },
        },
    },
    # ── 11. Whistleblower Case ────────────────────────────────────────
    {
        "name": "Whistleblower Case",
        "instruction": "Create a case for this anonymous whistleblower report of corporate fraud.",
        "input": (
            "Anonymous whistleblower report received via Protected Disclosures hotline. "
            "Allegation: CFO Richard Moyo (richard.moyo@transnet.net, ID 730415 5089 067, "
            "+27 11 308 2200) of Transnet SOC Ltd has been approving fictitious invoices from "
            "shell company BlueStar Logistics (Reg. 2019/348721/07) totalling R56,000,000 over "
            "18 months. Payments routed through FNB account 62847019352 and Standard Bank account "
            "041288736. Internal auditor Busisiwe Mthembu (busisiwe.m@transnet.net) flagged the "
            "irregularities on January 22, 2026. Case referred to the Hawks (ref: HAWKS-FRD-2026-0189). "
            "Whistleblower attorney: Adv. Craig Thompson, Cliffe Dekker Hofmeyr, "
            "craig.thompson@cdh.com, +27 11 562 1000."
        ),
        "expected_tools": ["create_case"],
        "pii_entities": {
            "PERSON": ["Richard Moyo", "Busisiwe Mthembu", "Adv. Craig Thompson"],
            "ORG": ["Transnet SOC Ltd", "BlueStar Logistics", "Cliffe Dekker Hofmeyr"],
            "EMAIL": ["richard.moyo@transnet.net", "busisiwe.m@transnet.net", "craig.thompson@cdh.com"],
            "PHONE": ["+27 11 308 2200", "+27 11 562 1000"],
            "GOVID": ["730415 5089 067", "2019/348721/07", "62847019352", "041288736"],
            "AMOUNT": ["R56,000,000"],
            "CASE_ID": ["HAWKS-FRD-2026-0189"],
        },
        "expected_args": {
            "create_case": {
                "case_title": lambda v: (
                    "whistleblower" in v.lower()
                    or "fraud" in v.lower()
                    or "fictitious" in v.lower()
                ),
                "client_name": lambda v: (
                    "anonymous" in v.lower()
                    or "whistleblower" in v.lower()
                    or _pii_or_token(v, "Busisiwe Mthembu", "PERSON")
                ),
                "case_type": lambda v: (
                    "fraud" in v.lower()
                    or "whistleblower" in v.lower()
                    or "corruption" in v.lower()
                ),
                "assigned_attorney": lambda v: _pii_or_token(v, "Adv. Craig Thompson", "PERSON"),
            },
        },
    },
    # ── 12. Licensing Agreement ───────────────────────────────────────
    {
        "name": "Licensing Agreement",
        "instruction": "Draft a software licensing clause based on these commercial terms.",
        "input": (
            "Software licensing agreement between Aethon Systems (Pty) Ltd and DataKinetic "
            "Corporation. Aethon grants DataKinetic a non-exclusive, worldwide licence to use "
            "the 'Aethon Cortex' AI analytics platform. Licence fee: USD 850,000/year with a "
            "3-year minimum commitment (total USD 2,550,000). Signed by Yuki Tanaka (CTO, Aethon, "
            "yuki.tanaka@aethonsys.com, +27 10 449 8812) and David Okonkwo (VP Engineering, "
            "DataKinetic, d.okonkwo@datakinetic.io, +1 415 983 2270). Sublicensing requires "
            "prior written consent. SLA guarantees 99.95% uptime. Source code escrow held at "
            "Iron Mountain, escrow ref IM-ESC-2026-3387. Governing law: South African law with "
            "arbitration at AFSA. Agreement drafted by Werksmans Attorneys, contact Adv. Lerato "
            "Mokoena (lerato.mokoena@werksmans.com)."
        ),
        "expected_tools": ["draft_contract_clause"],
        "pii_entities": {
            "PERSON": ["Yuki Tanaka", "David Okonkwo", "Adv. Lerato Mokoena"],
            "ORG": ["Aethon Systems", "DataKinetic Corporation", "Iron Mountain", "Werksmans Attorneys"],
            "EMAIL": ["yuki.tanaka@aethonsys.com", "d.okonkwo@datakinetic.io", "lerato.mokoena@werksmans.com"],
            "PHONE": ["+27 10 449 8812", "+1 415 983 2270"],
            "AMOUNT": ["USD 850,000", "USD 2,550,000"],
            "CASE_ID": ["IM-ESC-2026-3387"],
        },
        "expected_args": {
            "draft_contract_clause": {
                "clause_type": lambda v: "licen" in v.lower() or "software" in v.lower(),
                "parties": lambda v: (
                    (_pii_or_token(str(v), "Aethon Systems", "ORG"))
                    and (_pii_or_token(str(v), "DataKinetic Corporation", "ORG"))
                ),
                "terms": lambda v: (
                    (_pii_or_token(v, "USD 850,000", "AMOUNT") or _pii_or_token(v, "USD 2,550,000", "AMOUNT") or bool(_token_pattern("AMOUNT").search(v)))
                    and ("non-exclusive" in v.lower() or "worldwide" in v.lower() or "licen" in v.lower() or "uptime" in v.lower())
                ),
            },
        },
    },
]
