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
        "expected_args": {
            "lookup_contact": {
                "name": lambda v: "Jack Morrison" in v or "[PERSON_" in v,
            },
            "schedule_meeting": {
                "participants": lambda v: any(
                    "Jack Morrison" in p or "Thandi Mkhize" in p or "[PERSON_" in p
                    for p in v
                ),
                "agenda": lambda v: "signing" in v.lower() or "acquisition" in v.lower() or "[ORG_" in v,
            },
            "create_task": {
                "assignee": lambda v: (
                    "Thandi Mkhize" in v or "Sarah Chen" in v or "[PERSON_" in v
                ),
            },
            "transfer_funds": {
                "to_account": lambda v: "DE89 3704 0044 0532 0130 00" in v or "[BANKACCT_" in v,
                "amount": lambda v: "850" in v or "[AMOUNT_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Jack Morrison", "Adv. Thandi Mkhize", "Sarah Chen"],
            "AMOUNT": ["$8.5M", "$850K"],
            "BANKACCT": ["DE89 3704 0044 0532 0130 00", "6234 5678 901"],
            "EMAIL": ["jack@techstart.io"],
            "ORG": ["TechStart Inc"],
        },
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
        "expected_args": {
            "create_document": {
                "content": lambda v: (
                    "12.3" in v or "$12.3M" in v or "[AMOUNT_" in v
                ),
            },
            "send_email": {
                "to": lambda v: "m.park@sequoia.com" in v or "[EMAIL_" in v,
                "body": lambda v: (
                    "revenue" in v.lower() or "Q4" in v or "[AMOUNT_" in v
                ),
            },
            "schedule_meeting": {
                "participants": lambda v: any(
                    "Michael Park" in p or "Amanda Torres" in p or "Brian Walsh" in p or "[PERSON_" in p
                    for p in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": ["Sihle Dlamini", "Peter Wright", "Michael Park", "Amanda Torres", "Brian Walsh"],
            "AMOUNT": ["$12.3M", "$45M", "$2.1M", "$3.4M"],
            "EMAIL": ["s.dlamini@vodacom.co.za", "p.wright@standardbank.co.za", "m.park@sequoia.com"],
            "ORG": ["Vodacom", "Standard Bank"],
        },
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
        "expected_args": {
            "create_task": {
                "assignee": lambda v: (
                    "Daniel Botha" in v or "Precious Moloi" in v or "Lisa Park" in v or "[PERSON_" in v
                ),
            },
            "send_email": {
                "to": lambda v: "f.mthembu@absa.co.za" in v or "[EMAIL_" in v,
                "body": lambda v: (
                    "breach" in v.lower() or "incident" in v.lower() or "Absa" in v or "[ORG_" in v
                ),
            },
            "schedule_meeting": {
                "participants": lambda v: any(
                    "Daniel Botha" in p or "Lisa Park" in p or "Amanda Torres" in p
                    or "Precious Moloi" in p or "[PERSON_" in p
                    for p in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": ["Fumani Mthembu", "Daniel Botha", "Advocate Precious Moloi", "Lisa Park", "Amanda Torres"],
            "EMAIL": ["f.mthembu@absa.co.za"],
            "PHONE": ["+27 11 350 4567"],
            "ORG": ["Absa Group"],
        },
    },
    {
        "name": "Client Onboarding",
        "instruction": "Onboard the new enterprise client: create the welcome documentation, schedule a kickoff meeting, assign onboarding tasks, and send the welcome email.",
        "input": (
            "New enterprise client: Meridian Health Systems (contract value $4.2M/year). "
            "Primary contact is Dr. Nalini Kapoor, Chief Digital Officer, at n.kapoor@meridianhealth.com "
            "(+1 312 555 8901). Secondary contact: IT Director Ravi Sundaram, r.sundaram@meridianhealth.com. "
            "Kickoff meeting next Tuesday at 2 PM with Nalini, Ravi, our VP Sales David Okonkwo, "
            "and Solutions Architect Maria Fernandez. "
            "Tasks: 1) David Okonkwo — finalize SLA document by Monday (high), "
            "2) Maria Fernandez — provision staging environment by Wednesday (critical), "
            "3) Account Manager Yuki Tanaka — prepare training schedule by Thursday (medium). "
            "Create a welcome packet with contract summary, onboarding timeline, and support contacts. "
            "Send welcome email to Nalini with portal credentials (account ID: MHS-2026-0042)."
        ),
        "expected_tools": ["create_document", "schedule_meeting", "create_task", "send_email"],
        "expected_args": {
            "create_document": {
                "title": lambda v: "welcome" in v.lower() or "onboarding" in v.lower(),
                "content": lambda v: (
                    "Meridian" in v or "[ORG_" in v or "onboarding" in v.lower()
                ),
            },
            "schedule_meeting": {
                "participants": lambda v: any(
                    "Nalini Kapoor" in p or "Ravi Sundaram" in p
                    or "David Okonkwo" in p or "Maria Fernandez" in p or "[PERSON_" in p
                    for p in v
                ),
            },
            "create_task": {
                "assignee": lambda v: (
                    "David Okonkwo" in v or "Maria Fernandez" in v
                    or "Yuki Tanaka" in v or "[PERSON_" in v
                ),
            },
            "send_email": {
                "to": lambda v: "n.kapoor@meridianhealth.com" in v or "[EMAIL_" in v,
                "body": lambda v: (
                    "welcome" in v.lower() or "onboarding" in v.lower()
                    or "MHS-2026-0042" in v or "[ACCOUNTID_" in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": ["Dr. Nalini Kapoor", "Ravi Sundaram", "David Okonkwo", "Maria Fernandez", "Yuki Tanaka"],
            "EMAIL": ["n.kapoor@meridianhealth.com", "r.sundaram@meridianhealth.com"],
            "PHONE": ["+1 312 555 8901"],
            "AMOUNT": ["$4.2M"],
            "ORG": ["Meridian Health Systems"],
            "ACCOUNTID": ["MHS-2026-0042"],
        },
    },
    {
        "name": "Quarterly Close",
        "instruction": "Process the end-of-quarter close: create the financial summary report, email it to stakeholders, schedule the review meeting, and create follow-up tasks.",
        "input": (
            "Q1 2026 close: Total revenue $18.7M, EBITDA $4.1M, net margin 22%. "
            "Top client renewals: Naspers ($5.2M, renewed 3-year), MTN Group ($3.8M, renewed 2-year). "
            "Outstanding receivables: $2.3M from Sasol (contact CFO Lindiwe Nkosi, l.nkosi@sasol.co.za). "
            "Create financial summary report with P&L breakdown. "
            "Email report to board members: Chair Dr. Pieter van der Merwe (p.vandermerwe@board.co.za), "
            "and Treasurer Ayesha Patel (a.patel@board.co.za). "
            "Schedule Q1 review meeting for April 5th at 9 AM with CFO Priya Sharma, "
            "Controller James Oduya, and both board members. "
            "Tasks: 1) Priya Sharma — reconcile intercompany accounts by April 2nd (critical), "
            "2) James Oduya — prepare tax filing documents by April 10th (high), "
            "3) AR Manager Zanele Khumalo — follow up on Sasol receivables by April 3rd (high)."
        ),
        "expected_tools": ["create_document", "send_email", "schedule_meeting", "create_task"],
        "expected_args": {
            "create_document": {
                "title": lambda v: "financial" in v.lower() or "Q1" in v or "quarterly" in v.lower(),
                "content": lambda v: (
                    "18.7" in v or "$18.7M" in v or "[AMOUNT_" in v or "revenue" in v.lower()
                ),
            },
            "send_email": {
                "to": lambda v: (
                    "p.vandermerwe@board.co.za" in v or "a.patel@board.co.za" in v or "[EMAIL_" in v
                ),
                "body": lambda v: (
                    "Q1" in v or "financial" in v.lower() or "revenue" in v.lower() or "[AMOUNT_" in v
                ),
            },
            "schedule_meeting": {
                "participants": lambda v: any(
                    "Priya Sharma" in p or "James Oduya" in p
                    or "Pieter van der Merwe" in p or "Ayesha Patel" in p or "[PERSON_" in p
                    for p in v
                ),
            },
            "create_task": {
                "assignee": lambda v: (
                    "Priya Sharma" in v or "James Oduya" in v
                    or "Zanele Khumalo" in v or "[PERSON_" in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": [
                "Lindiwe Nkosi", "Dr. Pieter van der Merwe", "Ayesha Patel",
                "Priya Sharma", "James Oduya", "Zanele Khumalo",
            ],
            "EMAIL": ["l.nkosi@sasol.co.za", "p.vandermerwe@board.co.za", "a.patel@board.co.za"],
            "AMOUNT": ["$18.7M", "$4.1M", "$5.2M", "$3.8M", "$2.3M"],
            "ORG": ["Naspers", "MTN Group", "Sasol"],
        },
    },
    {
        "name": "Employee Offboarding",
        "instruction": "Process the departing employee: create access revocation tasks, send the farewell email, schedule the exit interview, and create the handover document.",
        "input": (
            "Employee departure: Senior Engineer Tomasz Kowalski (employee ID EMP-7721, "
            "SSN 318-42-7956) is leaving effective March 28th. Personal email: t.kowalski@gmail.com. "
            "Tasks: 1) IT Admin Grace Ndlovu — revoke all system access and recover equipment by March 27th (critical), "
            "2) HR Manager Fatima Al-Rashidi — process final payroll $14,200 and benefits termination by March 25th (high), "
            "3) Team Lead Oscar Mbeki — complete knowledge transfer sessions by March 26th (high). "
            "Schedule exit interview for March 27th at 3 PM with Fatima Al-Rashidi and "
            "HR Director Chen Wei. "
            "Send farewell email to the engineering team from Tomasz's manager Oscar Mbeki. "
            "Create handover document covering Tomasz's projects: Project Atlas and Project Beacon, "
            "including credentials for staging server (IP 10.0.5.42) and CI/CD pipeline access."
        ),
        "expected_tools": ["create_task", "send_email", "schedule_meeting", "create_document"],
        "expected_args": {
            "create_task": {
                "assignee": lambda v: (
                    "Grace Ndlovu" in v or "Fatima Al-Rashidi" in v
                    or "Oscar Mbeki" in v or "[PERSON_" in v
                ),
            },
            "send_email": {
                "body": lambda v: (
                    "Tomasz" in v or "farewell" in v.lower() or "[PERSON_" in v
                ),
            },
            "schedule_meeting": {
                "participants": lambda v: any(
                    "Fatima Al-Rashidi" in p or "Chen Wei" in p or "[PERSON_" in p
                    for p in v
                ),
                "agenda": lambda v: "exit" in v.lower() or "interview" in v.lower(),
            },
            "create_document": {
                "content": lambda v: (
                    "Atlas" in v or "Beacon" in v or "handover" in v.lower()
                    or "Tomasz" in v or "[PERSON_" in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": ["Tomasz Kowalski", "Grace Ndlovu", "Fatima Al-Rashidi", "Oscar Mbeki", "Chen Wei"],
            "EMAIL": ["t.kowalski@gmail.com"],
            "SSN": ["318-42-7956"],
            "EMPLOYEEID": ["EMP-7721"],
            "AMOUNT": ["$14,200"],
            "IPADDR": ["10.0.5.42"],
        },
    },
    {
        "name": "Product Launch",
        "instruction": "Prepare for the product launch: create a press release document, email the press contacts, schedule the launch event, and create marketing tasks.",
        "input": (
            "We're launching NebulaSync Pro on April 20th. Create a press release announcing the product — "
            "highlight AI-powered collaboration, $29/month pricing, and SOC 2 Type II certification. "
            "Email press contacts: tech journalist Ingrid Johansson at i.johansson@techcrunch.com "
            "(+46 70 234 5678) and analyst Kwame Asante at k.asante@gartner.com (+1 203 555 7890). "
            "Schedule the launch event for April 20th at 11 AM with VP Marketing Lucia Ferreira, "
            "Head of Product Dmitri Volkov, and CEO Raj Malhotra. Venue: Grand Ballroom, Sandton Convention Centre. "
            "Tasks: 1) Lucia Ferreira — finalize launch campaign assets by April 15th (critical), "
            "2) Social Media Lead Amara Osei — schedule 30 social posts by April 18th (high), "
            "3) Content Director Pavel Novak — prepare demo video and landing page by April 17th (high), "
            "4) PR Coordinator Sienna Blackwell — distribute press kits by April 19th (critical). "
            "Budget allocated: $175,000 for launch campaign. Company: NovaTech Solutions Ltd."
        ),
        "expected_tools": ["create_document", "send_email", "schedule_meeting", "create_task"],
        "expected_args": {
            "create_document": {
                "title": lambda v: "press" in v.lower() or "launch" in v.lower() or "nebula" in v.lower(),
                "content": lambda v: (
                    "NebulaSync" in v or "[ORG_" in v or "AI" in v or "$29" in v or "[AMOUNT_" in v
                ),
            },
            "send_email": {
                "to": lambda v: (
                    "i.johansson@techcrunch.com" in v or "k.asante@gartner.com" in v or "[EMAIL_" in v
                ),
                "body": lambda v: (
                    "launch" in v.lower() or "NebulaSync" in v or "[ORG_" in v
                ),
            },
            "schedule_meeting": {
                "participants": lambda v: any(
                    "Lucia Ferreira" in p or "Dmitri Volkov" in p
                    or "Raj Malhotra" in p or "[PERSON_" in p
                    for p in v
                ),
                "agenda": lambda v: "launch" in v.lower() or "nebula" in v.lower(),
            },
            "create_task": {
                "assignee": lambda v: (
                    "Lucia Ferreira" in v or "Amara Osei" in v
                    or "Pavel Novak" in v or "Sienna Blackwell" in v or "[PERSON_" in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": [
                "Ingrid Johansson", "Kwame Asante", "Lucia Ferreira",
                "Dmitri Volkov", "Raj Malhotra", "Amara Osei",
                "Pavel Novak", "Sienna Blackwell",
            ],
            "EMAIL": ["i.johansson@techcrunch.com", "k.asante@gartner.com"],
            "PHONE": ["+46 70 234 5678", "+1 203 555 7890"],
            "AMOUNT": ["$29/month", "$175,000"],
            "ORG": ["NovaTech Solutions Ltd", "NebulaSync Pro"],
            "LOCATION": ["Grand Ballroom, Sandton Convention Centre"],
        },
    },
    {
        "name": "Vendor Onboarding",
        "instruction": "Onboard the new vendor: create the contract document, look up the vendor contact, schedule a kickoff meeting, and process the initial deposit payment.",
        "input": (
            "New vendor: Pinnacle Data Services Pty Ltd, specializing in cloud infrastructure. "
            "Contract value $2.8M over 3 years, effective May 1st. "
            "Create the vendor services agreement covering SLA terms (99.95% uptime), "
            "data residency in Johannesburg and Frankfurt, and penalty clauses. "
            "Look up vendor contact Hendrik van Wyk, VP of Partnerships. "
            "His email: h.vanwyk@pinnacledata.co.za, phone: +27 21 487 3210. "
            "Schedule kickoff meeting for May 3rd at 10 AM with Hendrik, "
            "our Procurement Director Beatriz Gutierrez, Legal Counsel Adv. Nkosinathi Zulu, "
            "and CTO Yusuf Ibrahim. "
            "Process the initial deposit of $280,000 (10%) to Pinnacle's account "
            "IBAN GB29 NWBK 6016 1331 9268 19. Our account: ABSA 4051 2837 6490. "
            "Reference: VND-PINNACLE-2026-Q2. Vendor tax ID: ZA-9182736450."
        ),
        "expected_tools": ["create_document", "lookup_contact", "schedule_meeting", "transfer_funds"],
        "expected_args": {
            "create_document": {
                "title": lambda v: "contract" in v.lower() or "agreement" in v.lower() or "vendor" in v.lower(),
                "content": lambda v: (
                    "Pinnacle" in v or "[ORG_" in v or "99.95" in v or "SLA" in v
                ),
            },
            "lookup_contact": {
                "name": lambda v: "Hendrik van Wyk" in v or "[PERSON_" in v,
            },
            "schedule_meeting": {
                "participants": lambda v: any(
                    "Hendrik van Wyk" in p or "Beatriz Gutierrez" in p
                    or "Nkosinathi Zulu" in p or "Yusuf Ibrahim" in p or "[PERSON_" in p
                    for p in v
                ),
            },
            "transfer_funds": {
                "to_account": lambda v: "GB29 NWBK 6016 1331 9268 19" in v or "[BANKACCT_" in v,
                "amount": lambda v: "280" in v or "[AMOUNT_" in v,
            },
        },
        "pii_entities": {
            "PERSON": [
                "Hendrik van Wyk", "Beatriz Gutierrez",
                "Adv. Nkosinathi Zulu", "Yusuf Ibrahim",
            ],
            "EMAIL": ["h.vanwyk@pinnacledata.co.za"],
            "PHONE": ["+27 21 487 3210"],
            "AMOUNT": ["$2.8M", "$280,000"],
            "BANKACCT": ["GB29 NWBK 6016 1331 9268 19", "4051 2837 6490"],
            "ORG": ["Pinnacle Data Services Pty Ltd"],
            "TAXID": ["ZA-9182736450"],
            "LOCATION": ["Johannesburg", "Frankfurt"],
        },
    },
    {
        "name": "Compliance Remediation",
        "instruction": "Address the audit findings: create a remediation plan document, email the regulatory body, and assign remediation tasks to the team.",
        "input": (
            "Internal audit completed by Ernst & Young on March 1st identified 14 findings, "
            "5 critical. Audit report reference: AUD-2026-EY-0034. "
            "Create a remediation plan document addressing the critical findings: "
            "1) Inadequate encryption of PII data at rest, "
            "2) Missing access controls on financial systems, "
            "3) Non-compliant data retention policy (POPIA violation), "
            "4) Incomplete vendor risk assessments, "
            "5) Gaps in employee background verification records. "
            "Email the Information Regulator of South Africa — contact Adv. Pansy Tlakula "
            "at p.tlakula@inforegulator.org.za (+27 10 023 5200) with our remediation timeline. "
            "CC our external counsel Advocate Roshan Sobrun at r.sobrun@nortonrose.com. "
            "Tasks: 1) CISO Marguerite du Plessis — implement AES-256 encryption by April 30th (critical), "
            "2) IT Security Lead Tariq Hassan — deploy RBAC controls by April 15th (critical), "
            "3) DPO Chantal Rousseau — revise data retention policy by March 31st (high), "
            "4) Procurement Manager Olumide Adeyemi — complete vendor risk register by April 10th (high), "
            "5) HR Director Ananya Krishnamurthy — audit background check records by April 5th (critical). "
            "Total remediation budget: $420,000. Company: Emerald Financial Holdings."
        ),
        "expected_tools": ["create_document", "send_email", "create_task"],
        "expected_args": {
            "create_document": {
                "title": lambda v: "remediation" in v.lower() or "compliance" in v.lower() or "audit" in v.lower(),
                "content": lambda v: (
                    "encryption" in v.lower() or "POPIA" in v or "access control" in v.lower()
                    or "[ORG_" in v
                ),
            },
            "send_email": {
                "to": lambda v: (
                    "p.tlakula@inforegulator.org.za" in v or "[EMAIL_" in v
                ),
                "body": lambda v: (
                    "remediation" in v.lower() or "audit" in v.lower() or "finding" in v.lower()
                    or "[ORG_" in v
                ),
            },
            "create_task": {
                "assignee": lambda v: (
                    "Marguerite du Plessis" in v or "Tariq Hassan" in v
                    or "Chantal Rousseau" in v or "Olumide Adeyemi" in v
                    or "Ananya Krishnamurthy" in v or "[PERSON_" in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": [
                "Adv. Pansy Tlakula", "Advocate Roshan Sobrun",
                "Marguerite du Plessis", "Tariq Hassan", "Chantal Rousseau",
                "Olumide Adeyemi", "Ananya Krishnamurthy",
            ],
            "EMAIL": ["p.tlakula@inforegulator.org.za", "r.sobrun@nortonrose.com"],
            "PHONE": ["+27 10 023 5200"],
            "AMOUNT": ["$420,000"],
            "ORG": ["Ernst & Young", "Emerald Financial Holdings", "Information Regulator of South Africa"],
            "AUDITREF": ["AUD-2026-EY-0034"],
        },
    },
    {
        "name": "Board Election",
        "instruction": "Prepare for the board election: create the resolution document, email the board members with the agenda, and schedule the vote meeting.",
        "input": (
            "Annual board election for Kensington Capital Group plc. "
            "Create a formal board resolution document for the election of new directors. "
            "Nominees: 1) Dr. Abigail Thornton-Smythe, former CEO of Barclays Africa "
            "(DOB: 14 March 1968, passport UK-GBR-7723451), "
            "2) Professor Sibusiso Mabena, Dean of Wits Business School "
            "(DOB: 22 July 1975, ID: 7507225438082), "
            "3) Carmen Villanueva-Ortiz, Managing Partner at McKinsey Madrid "
            "(DOB: 9 November 1972, passport ESP-AAB429517). "
            "Email all current board members: Chair Lord Geoffrey Harrington at g.harrington@kensingtoncap.co.uk, "
            "Vice-Chair Dame Olivia Cartwright at o.cartwright@kensingtoncap.co.uk, "
            "and Company Secretary Thandiwe Maseko at t.maseko@kensingtoncap.co.uk (+44 20 7946 0321). "
            "Include nominee CVs, governance committee recommendations, and conflict-of-interest declarations. "
            "Schedule the election meeting for April 28th at 2 PM in the Boardroom, "
            "20 Finsbury Circus, London EC2M 7DQ. Attendees: all three current board members "
            "plus the three nominees. Quorum requires 4 of 6 members."
        ),
        "expected_tools": ["create_document", "send_email", "schedule_meeting"],
        "expected_args": {
            "create_document": {
                "title": lambda v: "resolution" in v.lower() or "election" in v.lower() or "board" in v.lower(),
                "content": lambda v: (
                    "Thornton" in v or "Mabena" in v or "Villanueva" in v
                    or "[PERSON_" in v or "nominee" in v.lower()
                ),
            },
            "send_email": {
                "to": lambda v: (
                    "g.harrington@kensingtoncap.co.uk" in v
                    or "o.cartwright@kensingtoncap.co.uk" in v
                    or "t.maseko@kensingtoncap.co.uk" in v or "[EMAIL_" in v
                ),
                "body": lambda v: (
                    "election" in v.lower() or "nominee" in v.lower()
                    or "resolution" in v.lower() or "[PERSON_" in v
                ),
            },
            "schedule_meeting": {
                "participants": lambda v: any(
                    "Geoffrey Harrington" in p or "Olivia Cartwright" in p
                    or "Thandiwe Maseko" in p or "Abigail Thornton" in p
                    or "Sibusiso Mabena" in p or "Carmen Villanueva" in p
                    or "[PERSON_" in p
                    for p in v
                ),
                "agenda": lambda v: "election" in v.lower() or "vote" in v.lower() or "board" in v.lower(),
            },
        },
        "pii_entities": {
            "PERSON": [
                "Dr. Abigail Thornton-Smythe", "Professor Sibusiso Mabena",
                "Carmen Villanueva-Ortiz", "Lord Geoffrey Harrington",
                "Dame Olivia Cartwright", "Thandiwe Maseko",
            ],
            "EMAIL": [
                "g.harrington@kensingtoncap.co.uk",
                "o.cartwright@kensingtoncap.co.uk",
                "t.maseko@kensingtoncap.co.uk",
            ],
            "PHONE": ["+44 20 7946 0321"],
            "DOB": ["14 March 1968", "22 July 1975", "9 November 1972"],
            "PASSPORT": ["UK-GBR-7723451", "ESP-AAB429517"],
            "NATIONALID": ["7507225438082"],
            "ORG": ["Kensington Capital Group plc", "Barclays Africa", "Wits Business School", "McKinsey Madrid"],
            "LOCATION": ["20 Finsbury Circus, London EC2M 7DQ"],
        },
    },
    {
        "name": "Grant Application",
        "instruction": "Prepare the grant submission: create the proposal document, email the foundation, create milestone tasks, and schedule the review meeting.",
        "input": (
            "Applying for the Wellspring Foundation Global Health Innovation Grant — $3.5M over 5 years. "
            "Proposal title: 'AI-Driven Diagnostic Platform for Rural Healthcare in Sub-Saharan Africa.' "
            "Create the proposal document with project summary, budget breakdown ($1.2M personnel, "
            "$800K equipment, $650K field operations, $500K data infrastructure, $350K admin), "
            "and impact metrics (target: 2M patients screened across 6 countries by Year 5). "
            "Principal Investigator: Prof. Zinhle Mthethwa, Dept. of Biomedical Engineering, "
            "University of Cape Town (z.mthethwa@uct.ac.za, +27 21 650 4321, ORCID: 0000-0002-8876-4532). "
            "Co-PI: Dr. Emmanuel Adjei-Mensah, Korle Bu Teaching Hospital, Accra "
            "(e.adjei@korlebu.edu.gh, +233 30 267 5890). "
            "Email the Foundation Program Director Katharine Winslow at k.winslow@wellspring.org "
            "(+1 415 555 2200) with the proposal summary and compliance attestation. "
            "CC grants coordinator Miriam Odhiambo at m.odhiambo@wellspring.org. "
            "Tasks: 1) Prof. Mthethwa — finalize ethics board approval (IRB ref: UCT-IRB-2026-0198) by April 10th (critical), "
            "2) Dr. Adjei-Mensah — secure field site partnerships by April 15th (high), "
            "3) Budget Analyst Farouk el-Amin — complete cost validation by April 8th (high), "
            "4) Research Coordinator Ingrid Bergström — compile team CVs and publications by April 5th (medium). "
            "Schedule proposal review meeting for April 3rd at 4 PM with all four team members "
            "and Faculty Dean Dr. Nomvula Dlamini."
        ),
        "expected_tools": ["create_document", "send_email", "create_task", "schedule_meeting"],
        "expected_args": {
            "create_document": {
                "title": lambda v: (
                    "proposal" in v.lower() or "grant" in v.lower()
                    or "diagnostic" in v.lower() or "AI" in v
                ),
                "content": lambda v: (
                    "1.2M" in v or "diagnostic" in v.lower() or "rural" in v.lower()
                    or "[AMOUNT_" in v or "Sub-Saharan" in v
                ),
            },
            "send_email": {
                "to": lambda v: "k.winslow@wellspring.org" in v or "[EMAIL_" in v,
                "body": lambda v: (
                    "grant" in v.lower() or "proposal" in v.lower()
                    or "Wellspring" in v or "[ORG_" in v
                ),
            },
            "create_task": {
                "assignee": lambda v: (
                    "Mthethwa" in v or "Adjei-Mensah" in v
                    or "Farouk el-Amin" in v or "Ingrid Bergström" in v or "[PERSON_" in v
                ),
            },
            "schedule_meeting": {
                "participants": lambda v: any(
                    "Mthethwa" in p or "Adjei-Mensah" in p
                    or "Farouk" in p or "Bergström" in p
                    or "Nomvula Dlamini" in p or "[PERSON_" in p
                    for p in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": [
                "Prof. Zinhle Mthethwa", "Dr. Emmanuel Adjei-Mensah",
                "Katharine Winslow", "Miriam Odhiambo",
                "Farouk el-Amin", "Ingrid Bergström", "Dr. Nomvula Dlamini",
            ],
            "EMAIL": [
                "z.mthethwa@uct.ac.za", "e.adjei@korlebu.edu.gh",
                "k.winslow@wellspring.org", "m.odhiambo@wellspring.org",
            ],
            "PHONE": ["+27 21 650 4321", "+233 30 267 5890", "+1 415 555 2200"],
            "AMOUNT": ["$3.5M", "$1.2M", "$800K", "$650K", "$500K", "$350K"],
            "ORG": [
                "Wellspring Foundation", "University of Cape Town",
                "Korle Bu Teaching Hospital",
            ],
            "ORCID": ["0000-0002-8876-4532"],
            "RESEARCHID": ["UCT-IRB-2026-0198"],
        },
    },
    {
        "name": "Crisis Communication",
        "instruction": "Handle the PR crisis: create a public statement document, email key stakeholders, schedule an emergency crisis meeting, and assign response tasks.",
        "input": (
            "PR crisis at Meridian Pharmaceuticals Inc: whistleblower report alleges contamination "
            "at the Durban manufacturing facility (Site ID: MFG-DUR-007) affecting Batch #LX-4419-B "
            "of CardioVex 50mg tablets, distributed to 340 pharmacies across KwaZulu-Natal. "
            "Create a public statement document acknowledging the report, outlining the voluntary recall, "
            "and describing corrective actions. Include crisis hotline: 0800 222 7463. "
            "Email stakeholders: SAHPRA (South African Health Products Regulatory Authority) liaison "
            "Dr. Bongani Khumalo at b.khumalo@sahpra.org.za (+27 12 501 0300), "
            "board chair Victoria Ashford-Cross at v.ashford@meridianpharma.com, "
            "and lead investor Magnus Lindqvist at m.lindqvist@nordicventures.se (+46 8 555 12340). "
            "Schedule emergency crisis meeting for tomorrow at 7 AM with CEO Dr. Priscilla Ndaba, "
            "General Counsel Advocate Themba Shabalala, VP Communications Hélène Dubois, "
            "and Head of Quality Assurance Dr. Kenji Watanabe. "
            "Tasks: 1) Dr. Watanabe — halt production line and quarantine remaining inventory by tonight (critical), "
            "2) Hélène Dubois — prepare media briefing and social media response by 6 AM (critical), "
            "3) Supply Chain Director Rosario Méndez — coordinate pharmacy recall logistics by noon (critical), "
            "4) Advocate Shabalala — prepare regulatory filings and liability assessment by end of day (high), "
            "5) Investor Relations VP Anika Petersen — draft investor communication by 9 AM (high)."
        ),
        "expected_tools": ["create_document", "send_email", "schedule_meeting", "create_task"],
        "expected_args": {
            "create_document": {
                "title": lambda v: (
                    "statement" in v.lower() or "crisis" in v.lower()
                    or "recall" in v.lower() or "response" in v.lower()
                ),
                "content": lambda v: (
                    "recall" in v.lower() or "contamination" in v.lower()
                    or "CardioVex" in v or "[ORG_" in v or "whistleblower" in v.lower()
                ),
            },
            "send_email": {
                "to": lambda v: (
                    "b.khumalo@sahpra.org.za" in v or "v.ashford@meridianpharma.com" in v
                    or "m.lindqvist@nordicventures.se" in v or "[EMAIL_" in v
                ),
                "body": lambda v: (
                    "recall" in v.lower() or "crisis" in v.lower()
                    or "contamination" in v.lower() or "[ORG_" in v
                ),
            },
            "schedule_meeting": {
                "participants": lambda v: any(
                    "Priscilla Ndaba" in p or "Themba Shabalala" in p
                    or "Hélène Dubois" in p or "Kenji Watanabe" in p
                    or "[PERSON_" in p
                    for p in v
                ),
                "agenda": lambda v: "crisis" in v.lower() or "emergency" in v.lower() or "recall" in v.lower(),
            },
            "create_task": {
                "assignee": lambda v: (
                    "Watanabe" in v or "Dubois" in v or "Méndez" in v
                    or "Shabalala" in v or "Anika Petersen" in v or "[PERSON_" in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": [
                "Dr. Bongani Khumalo", "Victoria Ashford-Cross", "Magnus Lindqvist",
                "Dr. Priscilla Ndaba", "Advocate Themba Shabalala",
                "Hélène Dubois", "Dr. Kenji Watanabe",
                "Rosario Méndez", "Anika Petersen",
            ],
            "EMAIL": [
                "b.khumalo@sahpra.org.za", "v.ashford@meridianpharma.com",
                "m.lindqvist@nordicventures.se",
            ],
            "PHONE": ["+27 12 501 0300", "+46 8 555 12340", "0800 222 7463"],
            "ORG": [
                "Meridian Pharmaceuticals Inc", "SAHPRA",
                "South African Health Products Regulatory Authority",
            ],
            "PRODUCTID": ["Batch #LX-4419-B", "CardioVex 50mg"],
            "SITEID": ["MFG-DUR-007"],
            "LOCATION": ["Durban", "KwaZulu-Natal"],
        },
    },
]
