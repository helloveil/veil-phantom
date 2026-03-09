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
    # ── Scenario 1: Wire Transfer ────────────────────────────────────────
    {
        "name": "Wire Transfer",
        "instruction": "Process this wire transfer request.",
        "input": (
            "Please wire R2.5 million from Standard Bank account 62847501234 to "
            "IBAN GB29 NWBK 6016 1331 9268 19. Reference: INV-2024-Q3. "
            "This is for the Johnson & Partners consulting fee."
        ),
        "expected_tools": ["transfer_funds"],
        "pii_entities": {
            "PERSON": ["Johnson & Partners"],
            "AMOUNT": ["R2.5 million"],
            "BANKACCT": ["62847501234", "GB29 NWBK 6016 1331 9268 19"],
        },
        "expected_args": {
            "transfer_funds": {
                "from_account": lambda v: "62847501234" in str(v) or "BANKACCT" in str(v),
                "to_account": lambda v: "GB29" in str(v) or "IBAN" in str(v) or "BANKACCT" in str(v),
                "amount": lambda v: "2.5" in str(v) or "AMOUNT" in str(v),
                "reference": lambda v: "INV-2024-Q3" in str(v),
            }
        },
    },
    # ── Scenario 2: Client Invoice ───────────────────────────────────────
    {
        "name": "Client Invoice",
        "instruction": "Create an invoice based on this meeting note.",
        "input": (
            "Wrap up with Priya Sharma at Tata Consulting. Bill them $47,500 for the Phase 2 "
            "data migration project. Her email is priya.sharma@tataconsulting.com. "
            "Net 30 terms, due April 15th 2026."
        ),
        "expected_tools": ["create_invoice"],
        "pii_entities": {
            "PERSON": ["Priya Sharma"],
            "ORG": ["Tata Consulting"],
            "AMOUNT": ["$47,500"],
            "EMAIL": ["priya.sharma@tataconsulting.com"],
        },
        "expected_args": {
            "create_invoice": {
                "client_name": lambda v: "Priya Sharma" in str(v) or "Tata" in str(v) or "PERSON" in str(v) or "ORG" in str(v),
                "client_email": lambda v: "priya.sharma" in str(v) or "EMAIL" in str(v),
                "amount": lambda v: "47,500" in str(v) or "47500" in str(v) or "AMOUNT" in str(v),
                "description": lambda v: "Phase 2" in str(v) or "data migration" in str(v),
            }
        },
    },
    # ── Scenario 3: Expense Report ───────────────────────────────────────
    {
        "name": "Expense Report",
        "instruction": "Submit this expense report for the employee.",
        "input": (
            "James Okafor spent $3,200 on client dinners during the Lagos trip. "
            "Credit card ending 4829. Receipt #REC-20260301. Also $1,850 for the Uber "
            "Black from OR Tambo to the Sandton office. His employee ID is EMP-4521."
        ),
        "expected_tools": ["submit_expense"],
        "pii_entities": {
            "PERSON": ["James Okafor"],
            "AMOUNT": ["$3,200", "$1,850"],
            "CREDITCARD": ["4829"],
            "ID": ["EMP-4521"],
        },
        "expected_args": {
            "submit_expense": {
                "employee": lambda v: "James Okafor" in str(v) or "PERSON" in str(v),
                "amount": lambda v: "3,200" in str(v) or "3200" in str(v) or "1,850" in str(v) or "AMOUNT" in str(v),
                "category": lambda v: "dinner" in str(v).lower() or "travel" in str(v).lower() or "client" in str(v).lower(),
            }
        },
    },
    # ── Scenario 4: Suspicious Activity ──────────────────────────────────
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
        "pii_entities": {
            "PERSON": ["Chen Wei"],
            "BANKACCT": ["7789234561"],
            "AMOUNT": ["$890,000"],
            "ID": ["850612 5234 083"],
            "EMAIL": ["compliance@meridianbank.co.za"],
        },
        "expected_args": {
            "flag_transaction": {
                "account": lambda v: "7789234561" in str(v) or "BANKACCT" in str(v),
                "reason": lambda v: "wire" in str(v).lower() or "suspicious" in str(v).lower() or "cayman" in str(v).lower(),
                "amount": lambda v: "890,000" in str(v) or "890000" in str(v) or "AMOUNT" in str(v),
            }
        },
    },
    # ── Scenario 5: Loan Application ────────────────────────────────────
    {
        "name": "Loan Application",
        "instruction": "Flag this loan application for compliance review before processing.",
        "input": (
            "New mortgage application from Maria Gonzalez-Rivera, SSN 471-83-2956. "
            "She is requesting $685,000 for a property at 42 Elm Street, Austin TX. "
            "Annual income $142,000, employed at Deloitte since 2019. "
            "Phone: +1-512-555-0147. Email: m.gonzalez@protonmail.com. "
            "Co-applicant: Roberto Gonzalez, SSN 523-67-8104, income $98,500."
        ),
        "expected_tools": ["flag_transaction"],
        "pii_entities": {
            "PERSON": ["Maria Gonzalez-Rivera", "Roberto Gonzalez"],
            "SSN": ["471-83-2956", "523-67-8104"],
            "AMOUNT": ["$685,000", "$142,000", "$98,500"],
            "ORG": ["Deloitte"],
            "PHONE": ["+1-512-555-0147"],
            "EMAIL": ["m.gonzalez@protonmail.com"],
            "ADDRESS": ["42 Elm Street, Austin TX"],
        },
        "expected_args": {
            "flag_transaction": {
                "account": lambda v: "Gonzalez" in str(v) or "PERSON" in str(v) or "mortgage" in str(v).lower(),
                "reason": lambda v: "loan" in str(v).lower() or "mortgage" in str(v).lower() or "application" in str(v).lower(),
                "amount": lambda v: "685,000" in str(v) or "685000" in str(v) or "AMOUNT" in str(v),
            }
        },
    },
    # ── Scenario 6: International Payment ────────────────────────────────
    {
        "name": "International Payment",
        "instruction": "Process this international SWIFT payment.",
        "input": (
            "Send EUR 1,250,000 from Deutsche Bank account DE89 3704 0044 0532 0130 00 "
            "to Nomura Holdings in Tokyo, account JP93 0009 0020 1234 5600 001. "
            "SWIFT/BIC: NOMUJPJT. Correspondent bank: JPMorgan Chase, SWIFT CHASUS33. "
            "Beneficiary contact: Takeshi Yamamoto, takeshi.y@nomura.co.jp, "
            "phone +81-3-3278-0500. Payment reference: FXHEDGE-2026-0042. "
            "Ordered by: Klaus Richter, CFO, klaus.richter@deutschebank.de."
        ),
        "expected_tools": ["transfer_funds"],
        "pii_entities": {
            "PERSON": ["Takeshi Yamamoto", "Klaus Richter"],
            "ORG": ["Nomura Holdings", "Deutsche Bank", "JPMorgan Chase"],
            "BANKACCT": ["DE89 3704 0044 0532 0130 00", "JP93 0009 0020 1234 5600 001"],
            "AMOUNT": ["EUR 1,250,000"],
            "EMAIL": ["takeshi.y@nomura.co.jp", "klaus.richter@deutschebank.de"],
            "PHONE": ["+81-3-3278-0500"],
            "SWIFT": ["NOMUJPJT", "CHASUS33"],
        },
        "expected_args": {
            "transfer_funds": {
                "from_account": lambda v: "DE89" in str(v) or "BANKACCT" in str(v) or "IBAN" in str(v),
                "to_account": lambda v: "JP93" in str(v) or "BANKACCT" in str(v) or "IBAN" in str(v),
                "amount": lambda v: "1,250,000" in str(v) or "1250000" in str(v) or "AMOUNT" in str(v),
                "currency": lambda v: "EUR" in str(v).upper(),
                "reference": lambda v: "FXHEDGE" in str(v) or "0042" in str(v),
            }
        },
    },
    # ── Scenario 7: Audit Trail ──────────────────────────────────────────
    {
        "name": "Audit Trail",
        "instruction": "Flag all suspicious transactions mentioned in this audit note.",
        "input": (
            "Audit finding AF-2026-118: Three accounts require immediate freezing. "
            "1) Account 3301-4488-7721 held by Fatima Al-Rashid (ID: QA-284719356), "
            "$214,000 wired to shell company Oceanic Trading LLC on 2026-02-28. "
            "2) Account 5509-2233-6645 held by Dmitri Volkov (passport RU-7283104), "
            "€187,500 structured deposits over 5 days. "
            "3) Account 8817-3300-1199 held by Ananya Krishnamurthy (Aadhaar 9182-7364-5510), "
            "INR 45,00,000 to undisclosed overseas recipient. "
            "Auditor: Sandra Williams, sandra.w@kpmg.com, ext. 4472."
        ),
        "expected_tools": ["flag_transaction"],
        "pii_entities": {
            "PERSON": ["Fatima Al-Rashid", "Dmitri Volkov", "Ananya Krishnamurthy", "Sandra Williams"],
            "BANKACCT": ["3301-4488-7721", "5509-2233-6645", "8817-3300-1199"],
            "ID": ["QA-284719356", "RU-7283104", "9182-7364-5510"],
            "AMOUNT": ["$214,000", "€187,500", "INR 45,00,000"],
            "ORG": ["Oceanic Trading LLC", "KPMG"],
            "EMAIL": ["sandra.w@kpmg.com"],
        },
        "expected_args": {
            "flag_transaction": {
                "account": lambda v: "3301" in str(v) or "5509" in str(v) or "8817" in str(v) or "BANKACCT" in str(v),
                "reason": lambda v: "audit" in str(v).lower() or "shell" in str(v).lower() or "structur" in str(v).lower() or "suspicious" in str(v).lower(),
                "amount": lambda v: "214,000" in str(v) or "187,500" in str(v) or "45,00,000" in str(v) or "AMOUNT" in str(v),
            }
        },
    },
    # ── Scenario 8: Forex Conversion ─────────────────────────────────────
    {
        "name": "Forex Conversion",
        "instruction": "Process this foreign exchange conversion and transfer.",
        "input": (
            "Convert and transfer GBP 340,000 from Barclays account GB82 BARC 2065 8791 4032 12 "
            "held by Abiodun Olatunde to Swiss franc equivalent in UBS account "
            "CH93 0076 2011 6238 5295 7. Beneficiary: Liesel Brugger, "
            "liesel.brugger@ubs.ch, phone +41-44-234-1111. "
            "FX rate locked at 1.1042 GBP/CHF. Dealer reference: FX-20260309-LDN-0781. "
            "Abiodun's contact: abiodun.olatunde@barclays.co.uk, passport NG-A04827156."
        ),
        "expected_tools": ["transfer_funds"],
        "pii_entities": {
            "PERSON": ["Abiodun Olatunde", "Liesel Brugger"],
            "BANKACCT": ["GB82 BARC 2065 8791 4032 12", "CH93 0076 2011 6238 5295 7"],
            "AMOUNT": ["GBP 340,000"],
            "EMAIL": ["liesel.brugger@ubs.ch", "abiodun.olatunde@barclays.co.uk"],
            "PHONE": ["+41-44-234-1111"],
            "ID": ["NG-A04827156"],
        },
        "expected_args": {
            "transfer_funds": {
                "from_account": lambda v: "GB82" in str(v) or "BANKACCT" in str(v) or "IBAN" in str(v),
                "to_account": lambda v: "CH93" in str(v) or "BANKACCT" in str(v) or "IBAN" in str(v),
                "amount": lambda v: "340,000" in str(v) or "340000" in str(v) or "AMOUNT" in str(v),
                "currency": lambda v: "GBP" in str(v).upper() or "CHF" in str(v).upper(),
                "reference": lambda v: "FX-20260309" in str(v) or "0781" in str(v),
            }
        },
    },
    # ── Scenario 9: Vendor Payment Batch ─────────────────────────────────
    {
        "name": "Vendor Payment Batch",
        "instruction": "Process this vendor payment batch from the company account.",
        "input": (
            "Pay the following vendors from Nakamura Corp operating account 4410-7823-5591-0036: "
            "1) Vendor: Oluwaseun Adeyemi at StellarTech Nigeria, NGN 18,750,000, "
            "account 0123456789 GTBank, email oluwaseun@stellartech.ng. "
            "2) Vendor: Isabelle Moreau at Données Rapides SARL, EUR 54,200, "
            "IBAN FR76 3000 6000 0112 3456 7890 189, isabelle.moreau@donneesrapides.fr. "
            "3) Vendor: Park Joon-ho at Sejong Analytics, KRW 67,500,000, "
            "account 110-432-789012 Shinhan Bank, joonho.park@sejong.kr. "
            "Authorized by: Yuki Nakamura, CFO, yuki.nakamura@nakamura-corp.jp."
        ),
        "expected_tools": ["transfer_funds"],
        "pii_entities": {
            "PERSON": ["Oluwaseun Adeyemi", "Isabelle Moreau", "Park Joon-ho", "Yuki Nakamura"],
            "ORG": ["Nakamura Corp", "StellarTech Nigeria", "Données Rapides SARL", "Sejong Analytics"],
            "BANKACCT": ["4410-7823-5591-0036", "0123456789", "FR76 3000 6000 0112 3456 7890 189", "110-432-789012"],
            "AMOUNT": ["NGN 18,750,000", "EUR 54,200", "KRW 67,500,000"],
            "EMAIL": ["oluwaseun@stellartech.ng", "isabelle.moreau@donneesrapides.fr", "joonho.park@sejong.kr", "yuki.nakamura@nakamura-corp.jp"],
        },
        "expected_args": {
            "transfer_funds": {
                "from_account": lambda v: "4410-7823-5591-0036" in str(v) or "BANKACCT" in str(v),
                "to_account": lambda v: "0123456789" in str(v) or "FR76" in str(v) or "110-432" in str(v) or "BANKACCT" in str(v),
                "amount": lambda v: "18,750,000" in str(v) or "54,200" in str(v) or "67,500,000" in str(v) or "AMOUNT" in str(v),
                "reference": lambda v: "vendor" in str(v).lower() or "batch" in str(v).lower() or "payment" in str(v).lower(),
            }
        },
    },
    # ── Scenario 10: Tax Filing ──────────────────────────────────────────
    {
        "name": "Tax Filing",
        "instruction": "Submit this expense for tax-deductible business costs.",
        "input": (
            "Ngozi Eze (employee ID TAX-EMP-8834) needs to file tax-deductible expenses "
            "for Q4 2025. Business travel to São Paulo: BRL 42,800 (receipt REC-TAX-90001). "
            "Home office equipment: R$15,600 (receipt REC-TAX-90002). "
            "Professional development course at INSEAD: EUR 8,950 (receipt REC-TAX-90003). "
            "Tax ID (CPF): 123.456.789-09. Accountant: Henrik Lindqvist, "
            "henrik.lindqvist@pwc.se, phone +46-8-555-3320. "
            "Reimbursement to Absa account 9205-1478-3360."
        ),
        "expected_tools": ["submit_expense"],
        "pii_entities": {
            "PERSON": ["Ngozi Eze", "Henrik Lindqvist"],
            "ID": ["TAX-EMP-8834", "123.456.789-09"],
            "AMOUNT": ["BRL 42,800", "R$15,600", "EUR 8,950"],
            "EMAIL": ["henrik.lindqvist@pwc.se"],
            "PHONE": ["+46-8-555-3320"],
            "BANKACCT": ["9205-1478-3360"],
        },
        "expected_args": {
            "submit_expense": {
                "employee": lambda v: "Ngozi Eze" in str(v) or "PERSON" in str(v),
                "amount": lambda v: "42,800" in str(v) or "15,600" in str(v) or "8,950" in str(v) or "AMOUNT" in str(v),
                "category": lambda v: "tax" in str(v).lower() or "deductible" in str(v).lower() or "travel" in str(v).lower() or "business" in str(v).lower(),
                "receipt_id": lambda v: "REC-TAX" in str(v) or "90001" in str(v) or "90002" in str(v) or "90003" in str(v),
            }
        },
    },
    # ── Scenario 11: Investment Allocation ───────────────────────────────
    {
        "name": "Investment Allocation",
        "instruction": "Flag this suspicious investment pattern for compliance review.",
        "input": (
            "Portfolio alert for client Rashida Mbeki, account INV-88432017. "
            "Over the past 72 hours, 14 rapid-fire trades totaling ZAR 12,400,000 "
            "were executed in thinly-traded micro-cap equities on the JSE. "
            "Pattern consistent with pump-and-dump manipulation. "
            "Client SSN equivalent (SA ID): 9507185012081. "
            "Linked brokerage account at Interactive Brokers: U7834291. "
            "Advisor on record: Konstantin Papadopoulos, k.papadopoulos@morganstanley.com, "
            "phone +27-11-282-4800. Compliance case ref: COMP-INV-2026-0055."
        ),
        "expected_tools": ["flag_transaction"],
        "pii_entities": {
            "PERSON": ["Rashida Mbeki", "Konstantin Papadopoulos"],
            "BANKACCT": ["INV-88432017", "U7834291"],
            "AMOUNT": ["ZAR 12,400,000"],
            "ID": ["9507185012081"],
            "EMAIL": ["k.papadopoulos@morganstanley.com"],
            "PHONE": ["+27-11-282-4800"],
            "ORG": ["Interactive Brokers", "Morgan Stanley"],
        },
        "expected_args": {
            "flag_transaction": {
                "account": lambda v: "INV-88432017" in str(v) or "U7834291" in str(v) or "BANKACCT" in str(v),
                "reason": lambda v: "pump" in str(v).lower() or "dump" in str(v).lower() or "manipulation" in str(v).lower() or "suspicious" in str(v).lower() or "rapid" in str(v).lower(),
                "amount": lambda v: "12,400,000" in str(v) or "12400000" in str(v) or "AMOUNT" in str(v),
            }
        },
    },
    # ── Scenario 12: Payroll Run ─────────────────────────────────────────
    {
        "name": "Payroll Run",
        "instruction": "Create an invoice for the outsourced payroll processing service.",
        "input": (
            "Generate invoice for ADP Payroll Services for processing March 2026 payroll. "
            "Contact: Mei-Ling Chen, mei-ling.chen@adp.com.sg, phone +65-6407-1200. "
            "Total payroll processed: SGD 2,340,000 for 187 employees. "
            "Service fee: SGD 28,500 (0.25% of payroll + SGD 22,650 flat). "
            "ADP tax registration: T08GA0032B. Invoice to be sent to "
            "Orion Dynamics Pte Ltd, accounts payable: ap@oriondynamics.sg. "
            "PO number: PO-OD-2026-0312. Payment terms: Net 15, due March 24th 2026. "
            "Approved by: Tariq Al-Farsi, VP Finance, tariq.alfarsi@oriondynamics.sg."
        ),
        "expected_tools": ["create_invoice"],
        "pii_entities": {
            "PERSON": ["Mei-Ling Chen", "Tariq Al-Farsi"],
            "ORG": ["ADP Payroll Services", "Orion Dynamics Pte Ltd"],
            "AMOUNT": ["SGD 2,340,000", "SGD 28,500", "SGD 22,650"],
            "EMAIL": ["mei-ling.chen@adp.com.sg", "ap@oriondynamics.sg", "tariq.alfarsi@oriondynamics.sg"],
            "PHONE": ["+65-6407-1200"],
            "ID": ["T08GA0032B"],
        },
        "expected_args": {
            "create_invoice": {
                "client_name": lambda v: "ADP" in str(v) or "Orion" in str(v) or "PERSON" in str(v) or "ORG" in str(v),
                "client_email": lambda v: "mei-ling.chen" in str(v) or "ap@oriondynamics" in str(v) or "EMAIL" in str(v),
                "amount": lambda v: "28,500" in str(v) or "28500" in str(v) or "AMOUNT" in str(v),
                "description": lambda v: "payroll" in str(v).lower() or "march" in str(v).lower() or "processing" in str(v).lower(),
                "due_date": lambda v: "March 24" in str(v) or "2026-03-24" in str(v) or "03/24" in str(v),
            }
        },
    },
    # ── Scenario 13: Insurance Claim ─────────────────────────────────────
    {
        "name": "Insurance Claim",
        "instruction": "Submit this expense for insurance reimbursement.",
        "input": (
            "Amara Diallo (employee ID HR-EMP-6217) is submitting an insurance "
            "reimbursement claim for emergency medical treatment in Nairobi. "
            "Hospital bill: KES 1,245,000 at Aga Khan University Hospital, "
            "receipt MED-REC-2026-4481. Policy number: AXA-KE-9920-4437-B. "
            "Additional pharmacy costs: KES 87,300, receipt PHARM-REC-2026-4482. "
            "Insurance provider contact: Beatrice Wanjiku, "
            "beatrice.wanjiku@axa-africa.co.ke, phone +254-20-286-5000. "
            "Amara's national ID: 32984517. Direct deposit to Equity Bank "
            "account 0190-2847-5563-01 for reimbursement."
        ),
        "expected_tools": ["submit_expense"],
        "pii_entities": {
            "PERSON": ["Amara Diallo", "Beatrice Wanjiku"],
            "ID": ["HR-EMP-6217", "AXA-KE-9920-4437-B", "32984517"],
            "AMOUNT": ["KES 1,245,000", "KES 87,300"],
            "EMAIL": ["beatrice.wanjiku@axa-africa.co.ke"],
            "PHONE": ["+254-20-286-5000"],
            "BANKACCT": ["0190-2847-5563-01"],
            "ORG": ["Aga Khan University Hospital", "AXA"],
        },
        "expected_args": {
            "submit_expense": {
                "employee": lambda v: "Amara Diallo" in str(v) or "PERSON" in str(v),
                "amount": lambda v: "1,245,000" in str(v) or "1245000" in str(v) or "87,300" in str(v) or "AMOUNT" in str(v),
                "category": lambda v: "insurance" in str(v).lower() or "medical" in str(v).lower() or "reimbursement" in str(v).lower() or "health" in str(v).lower(),
                "receipt_id": lambda v: "MED-REC" in str(v) or "PHARM-REC" in str(v) or "4481" in str(v) or "4482" in str(v),
            }
        },
    },
]
