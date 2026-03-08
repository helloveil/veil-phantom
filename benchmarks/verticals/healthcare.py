"""Healthcare vertical — patient records, appointments, prescriptions."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "schedule_appointment",
            "description": "Schedule a patient appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {"type": "string"},
                    "doctor": {"type": "string"},
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["patient_name", "doctor", "date", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_patient_record",
            "description": "Update a patient's medical record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {"type": "string"},
                    "patient_id": {"type": "string"},
                    "diagnosis": {"type": "string"},
                    "notes": {"type": "string"},
                    "prescriptions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["patient_name", "diagnosis"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_referral",
            "description": "Send a patient referral to a specialist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {"type": "string"},
                    "referring_doctor": {"type": "string"},
                    "specialist": {"type": "string"},
                    "specialist_email": {"type": "string"},
                    "reason": {"type": "string"},
                    "urgency": {"type": "string", "enum": ["routine", "urgent", "emergency"]},
                },
                "required": ["patient_name", "specialist", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "order_lab_test",
            "description": "Order laboratory tests for a patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {"type": "string"},
                    "tests": {"type": "array", "items": {"type": "string"}},
                    "ordering_physician": {"type": "string"},
                    "priority": {"type": "string", "enum": ["routine", "stat"]},
                },
                "required": ["patient_name", "tests"],
            },
        },
    },
]

SCENARIOS = [
    {
        "name": "Patient Follow-up",
        "instruction": "Schedule a follow-up appointment and update the patient record based on this clinical note.",
        "input": (
            "Patient Nomsa Dlamini (ID: PAT-20234) presented with persistent hypertension. "
            "BP readings 165/95. Prescribed Amlodipine 10mg daily. "
            "Follow-up with Dr. Patel in 2 weeks. Also order a lipid panel and HbA1c. "
            "Patient's medical aid number is MA-78452-GH. Contact: +27 73 456 7890."
        ),
        "expected_tools": ["update_patient_record", "schedule_appointment", "order_lab_test"],
        "pii_entities": ["Nomsa Dlamini", "PAT-20234", "Dr. Patel", "+27 73 456 7890", "MA-78452-GH"],
    },
    {
        "name": "Specialist Referral",
        "instruction": "Send an urgent referral based on this consultation note.",
        "input": (
            "Referring Thabo Mokoena (DOB: 15 March 1978) to Dr. Sarah Goldstein, oncology, "
            "at Groote Schuur Hospital. Suspicious mass found on CT scan. Patient's SA ID: "
            "780315 5234 083. Email Dr. Goldstein at s.goldstein@gsh.org.za. "
            "This is urgent — please expedite."
        ),
        "expected_tools": ["send_referral"],
        "pii_entities": ["Thabo Mokoena", "Dr. Sarah Goldstein", "780315 5234 083", "s.goldstein@gsh.org.za"],
    },
    {
        "name": "Lab Orders with History",
        "instruction": "Order the appropriate lab tests based on this patient history.",
        "input": (
            "Maria Santos, age 62, diabetic since 2010. Last HbA1c was 8.2% on Jan 5th. "
            "Currently on Metformin 1000mg and Insulin Glargine 20 units. "
            "Insurance: Discovery Health, policy DH-445891. "
            "Dr. Ahmed Patel ordering comprehensive metabolic panel, HbA1c, and urine microalbumin. "
            "Patient phone: 082-555-3344."
        ),
        "expected_tools": ["order_lab_test"],
        "pii_entities": ["Maria Santos", "DH-445891", "Dr. Ahmed Patel", "082-555-3344"],
    },
]
