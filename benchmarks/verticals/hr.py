"""HR vertical — employee onboarding, performance reviews, payroll."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "onboard_employee",
            "description": "Initiate employee onboarding process.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "department": {"type": "string"},
                    "start_date": {"type": "string"},
                    "salary": {"type": "string"},
                    "manager": {"type": "string"},
                    "email": {"type": "string"},
                    "benefits_plan": {"type": "string"},
                    "dependents": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "role", "department", "start_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_payroll_change",
            "description": "Process a salary or benefits change.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string"},
                    "employee_id": {"type": "string"},
                    "change_type": {"type": "string"},
                    "new_amount": {"type": "string"},
                    "effective_date": {"type": "string"},
                    "approved_by": {"type": "string"},
                    "reason": {"type": "string"},
                    "department": {"type": "string"},
                },
                "required": ["employee_name", "change_type", "new_amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_performance_review",
            "description": "Create a performance review record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {"type": "string"},
                    "reviewer": {"type": "string"},
                    "rating": {"type": "string", "enum": ["exceeds", "meets", "below", "unsatisfactory"]},
                    "summary": {"type": "string"},
                    "goals": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["employee_name", "reviewer", "rating", "summary"],
            },
        },
    },
]


def _pii_or_token(real_value, token_prefixes):
    """Return a lambda that checks if a value contains the real PII or a VeilPhantom token."""
    def check(v):
        v_str = str(v)
        # Accept if real PII present (pass-through mode)
        if real_value.lower() in v_str.lower():
            return True
        # Accept if any of the expected token patterns appear
        for prefix in token_prefixes:
            if prefix in v_str:
                return True
        return False
    return check


SCENARIOS = [
    # ── 1. New Hire Onboarding (existing) ────────────────────────────
    {
        "name": "New Hire Onboarding",
        "instruction": "Process this new hire onboarding.",
        "input": (
            "New hire: Aisha Moyo starting as Senior Data Scientist in the AI team on April 1st. "
            "Salary: R95,000/month. Reports to Dr. Liam O'Brien (Head of AI). "
            "Her email will be aisha.moyo@company.co.za. SA ID: 920815 5678 089. "
            "Bank details: FNB account 6234 8901 234 for salary deposits."
        ),
        "expected_tools": ["onboard_employee"],
        "pii_entities": {
            "PERSON": ["Aisha Moyo", "Dr. Liam O'Brien"],
            "AMOUNT": ["R95,000"],
            "EMAIL": ["aisha.moyo@company.co.za"],
            "GOVID": ["920815 5678 089"],
            "BANKACCT": ["6234 8901 234"],
        },
        "expected_args": {
            "onboard_employee": {
                "name": _pii_or_token("Aisha Moyo", ["[PERSON_"]),
                "role": lambda v: "data scientist" in v.lower(),
                "department": lambda v: "ai" in v.lower(),
                "salary": _pii_or_token("R95,000", ["[AMOUNT_"]),
                "manager": _pii_or_token("Dr. Liam O'Brien", ["[PERSON_"]),
                "email": _pii_or_token("aisha.moyo@company.co.za", ["[EMAIL_"]),
            },
        },
    },
    # ── 2. Salary Adjustment (existing) ──────────────────────────────
    {
        "name": "Salary Adjustment",
        "instruction": "Process the salary changes from this compensation review meeting.",
        "input": (
            "Compensation review approved by CFO Brian Walsh (EMP-001): "
            "1. Yuki Tanaka (EMP-234) — promote to VP Engineering, new salary $185,000/year. "
            "2. Carlos Mendez (EMP-567) — 12% raise to R72,000/month effective March 1st. "
            "HR contact: hr@company.com."
        ),
        "expected_tools": ["process_payroll_change"],
        "pii_entities": {
            "PERSON": ["Brian Walsh", "Yuki Tanaka", "Carlos Mendez"],
            "AMOUNT": ["$185,000", "R72,000"],
            "EMAIL": ["hr@company.com"],
            "EMPID": ["EMP-001", "EMP-234", "EMP-567"],
        },
        "expected_args": {
            "process_payroll_change": {
                "employee_name": _pii_or_token("Yuki Tanaka", ["[PERSON_"]),
                "new_amount": _pii_or_token("$185,000", ["[AMOUNT_"]),
                "approved_by": _pii_or_token("Brian Walsh", ["[PERSON_"]),
            },
        },
    },
    # ── 3. Performance Review (existing) ─────────────────────────────
    {
        "name": "Performance Review",
        "instruction": "Create a performance review based on these manager notes.",
        "input": (
            "Annual review for Fatima Al-Hassan (EMP-892). Reviewed by manager Sarah Chen. "
            "Rating: Exceeds expectations. Fatima led the migration of 2.3M user records "
            "with zero downtime. Promoted client satisfaction from 72% to 94%. "
            "Goals for next year: lead the API platform team, mentor 3 junior engineers. "
            "Contact: fatima.alhassan@company.com, +27 82 334 5567."
        ),
        "expected_tools": ["create_performance_review"],
        "pii_entities": {
            "PERSON": ["Fatima Al-Hassan", "Sarah Chen"],
            "EMAIL": ["fatima.alhassan@company.com"],
            "PHONE": ["+27 82 334 5567"],
            "EMPID": ["EMP-892"],
        },
        "expected_args": {
            "create_performance_review": {
                "employee_name": _pii_or_token("Fatima Al-Hassan", ["[PERSON_"]),
                "reviewer": _pii_or_token("Sarah Chen", ["[PERSON_"]),
                "rating": lambda v: v.lower() in ("exceeds", "exceeds expectations"),
                "summary": lambda v: len(v) > 20,
            },
        },
    },
    # ── 4. Termination Process (new) ─────────────────────────────────
    {
        "name": "Termination Process",
        "instruction": "Process this employee termination with final payroll and exit details.",
        "input": (
            "Termination notice: Raj Patel (EMP-411) is being terminated effective April 15th. "
            "Manager: Ingrid Bergström (VP Operations). Reason: Role elimination due to restructuring. "
            "Final salary payout: R128,500 including 6 weeks severance. Accumulated leave: 14 days "
            "valued at R31,200. Pension fund ref: PF-88210443. "
            "Send final documents to raj.patel@company.co.za. "
            "SA ID: 850623 5432 081. Bank: Nedbank account 1098 7654 321."
        ),
        "expected_tools": ["process_payroll_change"],
        "pii_entities": {
            "PERSON": ["Raj Patel", "Ingrid Bergström"],
            "AMOUNT": ["R128,500", "R31,200"],
            "EMAIL": ["raj.patel@company.co.za"],
            "GOVID": ["850623 5432 081"],
            "BANKACCT": ["1098 7654 321"],
            "EMPID": ["EMP-411"],
            "PENSIONREF": ["PF-88210443"],
        },
        "expected_args": {
            "process_payroll_change": {
                "employee_name": _pii_or_token("Raj Patel", ["[PERSON_"]),
                "change_type": lambda v: "termination" in v.lower() or "final" in v.lower(),
                "new_amount": _pii_or_token("R128,500", ["[AMOUNT_"]),
                "approved_by": _pii_or_token("Ingrid Bergström", ["[PERSON_"]),
            },
        },
    },
    # ── 5. Benefits Enrollment (new) ─────────────────────────────────
    {
        "name": "Benefits Enrollment",
        "instruction": "Enrol this new employee and their dependents in the company benefits plan.",
        "input": (
            "Benefits enrolment for new hire Priya Naidoo starting May 1st as Lead UX Designer "
            "in the Product team. She is enrolling in the Premium Family medical plan. "
            "Dependents: spouse Vikram Naidoo (DOB: 1988-11-23, ID: 881123 5098 087) and "
            "daughter Anaya Naidoo (DOB: 2019-06-15). "
            "Priya's SA ID: 900417 5234 083. Email: priya.naidoo@company.co.za. "
            "Monthly deduction: R4,850 from salary of R115,000/month. "
            "Emergency contact: Vikram Naidoo, +27 73 221 8890."
        ),
        "expected_tools": ["onboard_employee"],
        "pii_entities": {
            "PERSON": ["Priya Naidoo", "Vikram Naidoo", "Anaya Naidoo"],
            "GOVID": ["900417 5234 083", "881123 5098 087"],
            "EMAIL": ["priya.naidoo@company.co.za"],
            "PHONE": ["+27 73 221 8890"],
            "AMOUNT": ["R4,850", "R115,000"],
            "DOB": ["1988-11-23", "2019-06-15"],
        },
        "expected_args": {
            "onboard_employee": {
                "name": _pii_or_token("Priya Naidoo", ["[PERSON_"]),
                "role": lambda v: "ux" in v.lower() or "designer" in v.lower(),
                "department": lambda v: "product" in v.lower(),
                "benefits_plan": lambda v: "premium" in v.lower() or "family" in v.lower(),
                "dependents": lambda v: isinstance(v, list) and len(v) >= 1,
            },
        },
    },
    # ── 6. Internal Transfer (new) ───────────────────────────────────
    {
        "name": "Internal Transfer",
        "instruction": "Process this internal department transfer with the associated salary change.",
        "input": (
            "Internal transfer approved: Tomoko Hayashi (EMP-623) moving from Data Engineering "
            "to the Machine Learning team effective June 1st. New title: Senior ML Engineer. "
            "Salary adjustment from $142,000 to $168,000/year. Approved by CTO Elena Volkov. "
            "Tomoko's SSN: 412-78-9034. Corporate email: tomoko.hayashi@company.com. "
            "New manager: Dr. Samuel Okafor (EMP-102). "
            "Relocation allowance: $8,500 (one-time). Direct deposit: Chase acct 7823-4501-9922."
        ),
        "expected_tools": ["process_payroll_change"],
        "pii_entities": {
            "PERSON": ["Tomoko Hayashi", "Elena Volkov", "Dr. Samuel Okafor"],
            "AMOUNT": ["$142,000", "$168,000", "$8,500"],
            "EMAIL": ["tomoko.hayashi@company.com"],
            "GOVID": ["412-78-9034"],
            "BANKACCT": ["7823-4501-9922"],
            "EMPID": ["EMP-623", "EMP-102"],
        },
        "expected_args": {
            "process_payroll_change": {
                "employee_name": _pii_or_token("Tomoko Hayashi", ["[PERSON_"]),
                "change_type": lambda v: "transfer" in v.lower() or "promotion" in v.lower() or "adjustment" in v.lower(),
                "new_amount": _pii_or_token("$168,000", ["[AMOUNT_"]),
                "approved_by": _pii_or_token("Elena Volkov", ["[PERSON_"]),
                "department": lambda v: "ml" in v.lower() or "machine learning" in v.lower(),
            },
        },
    },
    # ── 7. Disciplinary Action (new) ─────────────────────────────────
    {
        "name": "Disciplinary Action",
        "instruction": "Create a performance review documenting this disciplinary action.",
        "input": (
            "Disciplinary review for Marcus Thompson (EMP-758). Reviewed by manager "
            "Dr. Amara Osei (Head of Compliance). Rating: Unsatisfactory. "
            "Marcus missed 3 consecutive project deadlines (Q3/Q4 2025) and failed to complete "
            "mandatory compliance training (cert ID: CT-20250112). Two prior verbal warnings "
            "were issued on 2025-08-10 and 2025-10-22. "
            "Outcome: Final written warning with 90-day performance improvement plan. "
            "Salary frozen at £78,500/year pending review. "
            "Goals: complete all overdue compliance modules, deliver Project Atlas milestone 2, "
            "attend weekly check-ins with manager. "
            "Employee contact: marcus.thompson@company.co.uk, +44 7911 234567. "
            "NI number: QQ 12 34 56 C."
        ),
        "expected_tools": ["create_performance_review"],
        "pii_entities": {
            "PERSON": ["Marcus Thompson", "Dr. Amara Osei"],
            "EMAIL": ["marcus.thompson@company.co.uk"],
            "PHONE": ["+44 7911 234567"],
            "AMOUNT": ["£78,500"],
            "GOVID": ["QQ 12 34 56 C"],
            "EMPID": ["EMP-758"],
            "DATE": ["2025-08-10", "2025-10-22"],
        },
        "expected_args": {
            "create_performance_review": {
                "employee_name": _pii_or_token("Marcus Thompson", ["[PERSON_"]),
                "reviewer": _pii_or_token("Dr. Amara Osei", ["[PERSON_"]),
                "rating": lambda v: v.lower() in ("unsatisfactory",),
                "summary": lambda v: "warning" in v.lower() or "deadline" in v.lower() or "disciplinary" in v.lower(),
                "goals": lambda v: isinstance(v, list) and len(v) >= 2,
            },
        },
    },
    # ── 8. Relocation Package (new) ────────────────────────────────
    {
        "name": "Relocation Package",
        "instruction": "Process the international relocation payroll changes for this employee.",
        "input": (
            "International relocation package for Mei-Ling Zhou (EMP-349). "
            "Mei-Ling is relocating from the Singapore office to London HQ effective July 1st. "
            "Visa sponsorship: Tier 2 General, reference GWF-2026-04812. "
            "Monthly housing allowance: £3,200 added to compensation. "
            "Salary adjustment from SGD 15,800/month to £9,750/month (GBP). "
            "One-time relocation bonus: £12,000 payable on start date. "
            "Approved by SVP Global Ops, Henrik Johansson (EMP-018). "
            "Mei-Ling's passport: E7234891 (Singapore). Personal email: meiling.zhou@gmail.com. "
            "Phone: +65 9123 4567. New UK bank: Barclays sort code 20-45-18, account 73019284. "
            "Tax reference (HMRC): 1234 56789."
        ),
        "expected_tools": ["process_payroll_change"],
        "pii_entities": {
            "PERSON": ["Mei-Ling Zhou", "Henrik Johansson"],
            "AMOUNT": ["£3,200", "SGD 15,800", "£9,750", "£12,000"],
            "EMAIL": ["meiling.zhou@gmail.com"],
            "PHONE": ["+65 9123 4567"],
            "GOVID": ["E7234891", "GWF-2026-04812", "1234 56789"],
            "BANKACCT": ["73019284"],
            "EMPID": ["EMP-349", "EMP-018"],
        },
        "expected_args": {
            "process_payroll_change": {
                "employee_name": _pii_or_token("Mei-Ling Zhou", ["[PERSON_"]),
                "change_type": lambda v: "relocation" in v.lower() or "transfer" in v.lower(),
                "new_amount": _pii_or_token("£9,750", ["[AMOUNT_"]),
                "approved_by": _pii_or_token("Henrik Johansson", ["[PERSON_"]),
            },
        },
    },
    # ── 9. Contractor Conversion (new) ─────────────────────────────
    {
        "name": "Contractor Conversion",
        "instruction": "Onboard this contractor as a full-time employee with benefits.",
        "input": (
            "Contractor-to-FTE conversion: Diego Ramirez (contractor ID: CTR-0782) is converting "
            "to full-time as Staff Backend Engineer in the Platform team, effective August 15th. "
            "Previous contractor rate: $125/hour via Acme Staffing (invoice ref INV-2026-3341). "
            "New FTE salary: $195,000/year plus 15% annual bonus target. "
            "Manager: Keiko Watanabe (EMP-215). Benefits: Gold medical + dental + vision. "
            "Diego's SSN: 528-93-4716. Personal email: diego.ramirez@outlook.com. "
            "Phone: +1 (512) 867-5309. Direct deposit: Wells Fargo routing 121000248, "
            "account 4019 2837 5501. Emergency contact: Sofia Ramirez, +1 (512) 555-0142."
        ),
        "expected_tools": ["onboard_employee"],
        "pii_entities": {
            "PERSON": ["Diego Ramirez", "Keiko Watanabe", "Sofia Ramirez"],
            "AMOUNT": ["$125", "$195,000"],
            "EMAIL": ["diego.ramirez@outlook.com"],
            "PHONE": ["+1 (512) 867-5309", "+1 (512) 555-0142"],
            "GOVID": ["528-93-4716"],
            "BANKACCT": ["121000248", "4019 2837 5501"],
            "EMPID": ["CTR-0782", "EMP-215"],
        },
        "expected_args": {
            "onboard_employee": {
                "name": _pii_or_token("Diego Ramirez", ["[PERSON_"]),
                "role": lambda v: "backend" in v.lower() or "engineer" in v.lower(),
                "department": lambda v: "platform" in v.lower(),
                "salary": _pii_or_token("$195,000", ["[AMOUNT_"]),
                "manager": _pii_or_token("Keiko Watanabe", ["[PERSON_"]),
                "email": _pii_or_token("diego.ramirez@outlook.com", ["[EMAIL_"]),
                "benefits_plan": lambda v: "gold" in v.lower() or "medical" in v.lower(),
            },
        },
    },
    # ── 10. Parental Leave (new) ───────────────────────────────────
    {
        "name": "Parental Leave",
        "instruction": "Process the parental leave payroll adjustments and coverage plan.",
        "input": (
            "Parental leave request: Natasha Okonkwo (EMP-531) is going on maternity leave "
            "from September 1st to February 28th (6 months). Current salary: R138,000/month. "
            "Company policy: 100% pay for first 4 months, 60% (R82,800/month) for remaining 2 months. "
            "UIF maternity benefit reference: UIF-2026-08-44210. "
            "Temporary coverage: her role (Senior Product Manager, Growth squad) will be covered by "
            "acting manager James Fitzgerald (EMP-290). "
            "Natasha's SA ID: 910305 5812 084. Email: natasha.okonkwo@company.co.za. "
            "Phone: +27 61 445 9923. Medical aid: Discovery Health, membership D-90281437. "
            "Bank: Standard Bank account 2810 4493 776."
        ),
        "expected_tools": ["process_payroll_change"],
        "pii_entities": {
            "PERSON": ["Natasha Okonkwo", "James Fitzgerald"],
            "AMOUNT": ["R138,000", "R82,800"],
            "EMAIL": ["natasha.okonkwo@company.co.za"],
            "PHONE": ["+27 61 445 9923"],
            "GOVID": ["910305 5812 084", "UIF-2026-08-44210"],
            "BANKACCT": ["2810 4493 776"],
            "EMPID": ["EMP-531", "EMP-290"],
            "MEDICALID": ["D-90281437"],
        },
        "expected_args": {
            "process_payroll_change": {
                "employee_name": _pii_or_token("Natasha Okonkwo", ["[PERSON_"]),
                "change_type": lambda v: "leave" in v.lower() or "maternity" in v.lower() or "parental" in v.lower(),
                "new_amount": _pii_or_token("R82,800", ["[AMOUNT_"]),
                "reason": lambda v: "maternity" in v.lower() or "parental" in v.lower() or "leave" in v.lower(),
            },
        },
    },
    # ── 11. Team Reorganization (new) ──────────────────────────────
    {
        "name": "Team Reorganization",
        "instruction": "Create interim performance reviews for employees affected by this team reorganization.",
        "input": (
            "Team reorganization effective October 1st — the Data Platform team is splitting into "
            "two squads. Interim reviews required for transitioning employees. "
            "Employee: Oluwaseun Adeyemi (EMP-644), currently under manager Claudia Bianchi (EMP-188). "
            "Moving to the new Real-Time Analytics squad under new manager Dr. Ravi Kapoor (EMP-072). "
            "Oluwaseun has been performing at 'Meets Expectations' level. Key achievements: "
            "designed the streaming pipeline processing 4.2M events/day, reduced data lag from "
            "45 min to under 90 seconds. Goals for new squad: own the Flink cluster migration, "
            "establish SLAs for real-time dashboards, onboard 2 new team members. "
            "Contact: oluwaseun.adeyemi@company.com, +234 803 555 7721. "
            "Employee ID badge: BDG-2024-0644. Salary: ₦18,500,000/year."
        ),
        "expected_tools": ["create_performance_review"],
        "pii_entities": {
            "PERSON": ["Oluwaseun Adeyemi", "Claudia Bianchi", "Dr. Ravi Kapoor"],
            "EMAIL": ["oluwaseun.adeyemi@company.com"],
            "PHONE": ["+234 803 555 7721"],
            "AMOUNT": ["₦18,500,000"],
            "EMPID": ["EMP-644", "EMP-188", "EMP-072"],
        },
        "expected_args": {
            "create_performance_review": {
                "employee_name": _pii_or_token("Oluwaseun Adeyemi", ["[PERSON_"]),
                "reviewer": _pii_or_token("Claudia Bianchi", ["[PERSON_"]),
                "rating": lambda v: v.lower() in ("meets", "meets expectations"),
                "summary": lambda v: "reorgani" in v.lower() or "transition" in v.lower() or "pipeline" in v.lower(),
                "goals": lambda v: isinstance(v, list) and len(v) >= 2,
            },
        },
    },
    # ── 12. Equity Grant (new) ─────────────────────────────────────
    {
        "name": "Equity Grant",
        "instruction": "Process this stock option equity grant with vesting schedule as a payroll change.",
        "input": (
            "Equity grant approval for Linh Tran (EMP-917). Approved by CEO Amanda Blackwell (EMP-001). "
            "Grant: 12,000 stock options at strike price $42.75/share. "
            "Total grant value at current FMV: $513,000. Vesting schedule: 4-year with 1-year cliff — "
            "25% vests on October 1st 2027, remainder monthly over 36 months. "
            "Grant ID: EQ-2026-00384. Board resolution ref: BR-2026-09-12. "
            "Linh's current salary: $210,000/year, department: Engineering (Core Infrastructure). "
            "SSN: 671-42-8903. Personal email: linh.t.tran@protonmail.com. "
            "Phone: +1 (650) 334-8821. Brokerage: E*Trade account ET-88421073. "
            "Home address: 1847 Middlefield Rd, Palo Alto, CA 94301."
        ),
        "expected_tools": ["process_payroll_change"],
        "pii_entities": {
            "PERSON": ["Linh Tran", "Amanda Blackwell"],
            "AMOUNT": ["$42.75", "$513,000", "$210,000"],
            "EMAIL": ["linh.t.tran@protonmail.com"],
            "PHONE": ["+1 (650) 334-8821"],
            "GOVID": ["671-42-8903"],
            "EMPID": ["EMP-917", "EMP-001"],
            "ADDRESS": ["1847 Middlefield Rd, Palo Alto, CA 94301"],
            "FINACCT": ["ET-88421073"],
        },
        "expected_args": {
            "process_payroll_change": {
                "employee_name": _pii_or_token("Linh Tran", ["[PERSON_"]),
                "change_type": lambda v: "equity" in v.lower() or "stock" in v.lower() or "grant" in v.lower(),
                "new_amount": _pii_or_token("$513,000", ["[AMOUNT_"]),
                "approved_by": _pii_or_token("Amanda Blackwell", ["[PERSON_"]),
                "reason": lambda v: "vest" in v.lower() or "equity" in v.lower() or "stock" in v.lower() or "option" in v.lower(),
            },
        },
    },
    # ── 13. Exit Interview (new) ───────────────────────────────────
    {
        "name": "Exit Interview",
        "instruction": "Create a final performance review based on this departing employee's exit interview.",
        "input": (
            "Exit interview summary for Brendan O'Sullivan (EMP-405), departing November 30th. "
            "Final review by manager Anika Desai (Director of Sales, EMP-139). "
            "Rating: Meets expectations. Brendan served 4 years as Senior Account Executive, "
            "consistently hitting 110%+ of quota. Lifetime revenue contribution: €2,340,000. "
            "Departure reason: joining competitor (3-month non-compete clause applies, ref NCC-2022-0405). "
            "Feedback highlights: praised team culture and mentorship, cited limited growth "
            "opportunities as primary reason for leaving. Recommends improving IC promotion track. "
            "Exit checklist: laptop returned, badge BDG-2022-0405 deactivated, CRM access revoked. "
            "Forwarding email: brendan.osullivan@gmail.com. Phone: +353 87 234 5678. "
            "PPS number: 8234567TA. Final commission payout: €18,750 to AIB account IE29AIBK93115212345678."
        ),
        "expected_tools": ["create_performance_review"],
        "pii_entities": {
            "PERSON": ["Brendan O'Sullivan", "Anika Desai"],
            "AMOUNT": ["€2,340,000", "€18,750"],
            "EMAIL": ["brendan.osullivan@gmail.com"],
            "PHONE": ["+353 87 234 5678"],
            "GOVID": ["8234567TA"],
            "BANKACCT": ["IE29AIBK93115212345678"],
            "EMPID": ["EMP-405", "EMP-139"],
        },
        "expected_args": {
            "create_performance_review": {
                "employee_name": _pii_or_token("Brendan O'Sullivan", ["[PERSON_"]),
                "reviewer": _pii_or_token("Anika Desai", ["[PERSON_"]),
                "rating": lambda v: v.lower() in ("meets", "meets expectations"),
                "summary": lambda v: "exit" in v.lower() or "depart" in v.lower() or "leaving" in v.lower() or "quota" in v.lower(),
            },
        },
    },
]
