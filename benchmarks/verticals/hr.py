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

SCENARIOS = [
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
        "pii_entities": ["Aisha Moyo", "Dr. Liam O'Brien", "R95,000", "aisha.moyo@company.co.za",
                         "920815 5678 089", "6234 8901 234"],
    },
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
        "pii_entities": ["Brian Walsh", "Yuki Tanaka", "Carlos Mendez", "$185,000", "R72,000", "hr@company.com"],
    },
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
        "pii_entities": ["Fatima Al-Hassan", "Sarah Chen", "fatima.alhassan@company.com", "+27 82 334 5567"],
    },
]
