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
    # ── Existing scenario 1 ──────────────────────────────────────────────
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
        "expected_args": {
            "update_patient_record": {
                "patient_name": lambda v: "Nomsa" in str(v) or "PERSON" in str(v),
                "patient_id": lambda v: "PAT-20234" in str(v) or "MEDICAL_ID" in str(v) or "ID" in str(v),
                "diagnosis": lambda v: "hypertension" in str(v).lower(),
            },
            "schedule_appointment": {
                "patient_name": lambda v: "Nomsa" in str(v) or "PERSON" in str(v),
                "doctor": lambda v: "Patel" in str(v) or "PERSON" in str(v),
            },
            "order_lab_test": {
                "patient_name": lambda v: "Nomsa" in str(v) or "PERSON" in str(v),
            },
        },
        "pii_entities": {
            "PERSON": ["Nomsa Dlamini", "Dr. Patel"],
            "MEDICAL_ID": ["PAT-20234"],
            "PHONE": ["+27 73 456 7890"],
            "INSURANCE_ID": ["MA-78452-GH"],
        },
    },
    # ── Existing scenario 2 ──────────────────────────────────────────────
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
        "expected_args": {
            "send_referral": {
                "patient_name": lambda v: "Thabo" in str(v) or "PERSON" in str(v),
                "specialist": lambda v: "Goldstein" in str(v) or "PERSON" in str(v),
                "specialist_email": lambda v: "goldstein" in str(v) or "EMAIL" in str(v),
                "urgency": lambda v: str(v) in ("urgent", "emergency"),
                "reason": lambda v: "mass" in str(v).lower() or "CT" in str(v),
            },
        },
        "pii_entities": {
            "PERSON": ["Thabo Mokoena", "Dr. Sarah Goldstein"],
            "DATE_OF_BIRTH": ["15 March 1978"],
            "NATIONAL_ID": ["780315 5234 083"],
            "EMAIL": ["s.goldstein@gsh.org.za"],
        },
    },
    # ── Existing scenario 3 ──────────────────────────────────────────────
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
        "expected_args": {
            "order_lab_test": {
                "patient_name": lambda v: "Maria" in str(v) or "PERSON" in str(v),
                "ordering_physician": lambda v: "Ahmed" in str(v) or "Patel" in str(v) or "PERSON" in str(v),
            },
        },
        "pii_entities": {
            "PERSON": ["Maria Santos", "Dr. Ahmed Patel"],
            "INSURANCE_ID": ["DH-445891"],
            "PHONE": ["082-555-3344"],
        },
    },
    # ── New scenario 4 ───────────────────────────────────────────────────
    {
        "name": "Emergency Admission",
        "instruction": "Admit this ER patient: update their medical record and order the necessary lab work.",
        "input": (
            "ER admission for Lindiwe Nkosi (ID: PAT-90817), 34-year-old female, "
            "brought in by ambulance after a severe allergic reaction (anaphylaxis to penicillin). "
            "Known allergies: penicillin, shellfish. Currently stabilised with epinephrine. "
            "Insurance: Bonitas Medical Fund, member number BM-336710-X. "
            "Emergency contact: husband Sipho Nkosi, cell +27 82 901 2345. "
            "Home address: 14 Protea Lane, Sandton, 2196. "
            "Ordering physician Dr. Fatima Al-Rashid. STAT CBC, BMP, and tryptase levels."
        ),
        "expected_tools": ["update_patient_record", "order_lab_test"],
        "expected_args": {
            "update_patient_record": {
                "patient_name": lambda v: "Lindiwe" in str(v) or "PERSON" in str(v),
                "patient_id": lambda v: "PAT-90817" in str(v) or "MEDICAL_ID" in str(v) or "ID" in str(v),
                "diagnosis": lambda v: "anaphylaxis" in str(v).lower() or "allergic" in str(v).lower(),
            },
            "order_lab_test": {
                "patient_name": lambda v: "Lindiwe" in str(v) or "PERSON" in str(v),
                "ordering_physician": lambda v: "Al-Rashid" in str(v) or "Fatima" in str(v) or "PERSON" in str(v),
                "priority": lambda v: str(v) == "stat",
            },
        },
        "pii_entities": {
            "PERSON": ["Lindiwe Nkosi", "Sipho Nkosi", "Dr. Fatima Al-Rashid"],
            "MEDICAL_ID": ["PAT-90817"],
            "INSURANCE_ID": ["BM-336710-X"],
            "PHONE": ["+27 82 901 2345"],
            "ADDRESS": ["14 Protea Lane, Sandton, 2196"],
        },
    },
    # ── New scenario 5 ───────────────────────────────────────────────────
    {
        "name": "Prescription Renewal",
        "instruction": "Update the patient record with the renewed prescriptions from this pharmacy request.",
        "input": (
            "Prescription renewal for Rajesh Govender (DOB: 22 August 1965), "
            "chronic patient at Mediclinic Morningside. SA ID: 650822 5198 087. "
            "Current medications due for refill: Atorvastatin 40mg (30-day supply), "
            "Losartan 100mg (30-day supply), Aspirin 81mg (90-day supply). "
            "Prescribing physician: Dr. Lerato Molefe, practice number PR-0044231. "
            "Pharmacy: Dis-Chem Sandton City, dispensing pharmacist licence RPH-7821. "
            "Patient email: r.govender@webmail.co.za. Medical aid: Momentum Health, "
            "member MH-2290054."
        ),
        "expected_tools": ["update_patient_record"],
        "expected_args": {
            "update_patient_record": {
                "patient_name": lambda v: "Rajesh" in str(v) or "Govender" in str(v) or "PERSON" in str(v),
                "diagnosis": lambda v: "renewal" in str(v).lower() or "chronic" in str(v).lower() or "refill" in str(v).lower(),
                "prescriptions": lambda v: isinstance(v, list) and len(v) >= 2,
            },
        },
        "pii_entities": {
            "PERSON": ["Rajesh Govender", "Dr. Lerato Molefe"],
            "DATE_OF_BIRTH": ["22 August 1965"],
            "NATIONAL_ID": ["650822 5198 087"],
            "EMAIL": ["r.govender@webmail.co.za"],
            "INSURANCE_ID": ["MH-2290054"],
            "LICENCE_NUMBER": ["PR-0044231", "RPH-7821"],
        },
    },
    # ── New scenario 6 ───────────────────────────────────────────────────
    {
        "name": "Insurance Pre-Auth",
        "instruction": "Send a referral requesting pre-authorization for the planned procedure.",
        "input": (
            "Pre-authorization request for patient Amahle Zulu (ID: PAT-55203). "
            "Procedure: elective laparoscopic cholecystectomy, CPT code 47562. "
            "ICD-10 diagnosis: K80.20 (calculus of gallbladder without obstruction). "
            "Referring surgeon: Dr. Jonathan van der Merwe, HPCSA reg MP-0389216. "
            "Send to Discovery Health pre-auth department, fax 011-539-2800, "
            "email preauth@discovery.co.za. "
            "Patient Discovery Health plan: KeyCare Plus, member number DH-8834510. "
            "Patient cell: +27 61 778 9012. SA ID: 910414 0267 085. "
            "Estimated cost: R45,000. Planned admission date: 15 April 2026 "
            "at Netcare Milpark Hospital."
        ),
        "expected_tools": ["send_referral"],
        "expected_args": {
            "send_referral": {
                "patient_name": lambda v: "Amahle" in str(v) or "Zulu" in str(v) or "PERSON" in str(v),
                "referring_doctor": lambda v: "van der Merwe" in str(v) or "Jonathan" in str(v) or "PERSON" in str(v),
                "specialist_email": lambda v: "preauth" in str(v) or "EMAIL" in str(v),
                "reason": lambda v: "cholecystectomy" in str(v).lower() or "pre-auth" in str(v).lower() or "gallbladder" in str(v).lower(),
            },
        },
        "pii_entities": {
            "PERSON": ["Amahle Zulu", "Dr. Jonathan van der Merwe"],
            "MEDICAL_ID": ["PAT-55203"],
            "NATIONAL_ID": ["910414 0267 085"],
            "INSURANCE_ID": ["DH-8834510"],
            "PHONE": ["+27 61 778 9012"],
            "EMAIL": ["preauth@discovery.co.za"],
            "FAX": ["011-539-2800"],
            "LICENCE_NUMBER": ["MP-0389216"],
        },
    },
    # ── New scenario 7 ───────────────────────────────────────────────────
    {
        "name": "Post-Surgery Follow-up",
        "instruction": "Schedule a post-operative follow-up and refer the patient to physical therapy.",
        "input": (
            "Patient Bongani Mthembu (ID: PAT-61438) was discharged on 2 March 2026 "
            "following a right total knee replacement (CPT 27447). Surgery performed by "
            "Dr. Annelize Botha at Life Fourways Hospital. Patient is recovering well but "
            "requires a 2-week post-op follow-up with Dr. Botha and a referral to "
            "physiotherapist Keegan O'Sullivan at PhysioFit Bryanston, "
            "email keegan@physiofitsa.co.za. SA ID: 880719 5483 081. "
            "Medical aid: Fedhealth, member number FH-1127643. "
            "Patient cell: +27 79 334 5612. Home address: 8 Jacaranda Crescent, Lonehill, 2062."
        ),
        "expected_tools": ["schedule_appointment", "send_referral"],
        "expected_args": {
            "schedule_appointment": {
                "patient_name": lambda v: "Bongani" in str(v) or "PERSON" in str(v),
                "doctor": lambda v: "Botha" in str(v) or "PERSON" in str(v),
                "reason": lambda v: "follow-up" in str(v).lower() or "post-op" in str(v).lower() or "knee" in str(v).lower(),
            },
            "send_referral": {
                "patient_name": lambda v: "Bongani" in str(v) or "PERSON" in str(v),
                "specialist": lambda v: "O'Sullivan" in str(v) or "Keegan" in str(v) or "PERSON" in str(v),
                "specialist_email": lambda v: "keegan" in str(v) or "EMAIL" in str(v),
                "reason": lambda v: "physio" in str(v).lower() or "knee" in str(v).lower() or "rehabilitation" in str(v).lower(),
            },
        },
        "pii_entities": {
            "PERSON": ["Bongani Mthembu", "Dr. Annelize Botha", "Keegan O'Sullivan"],
            "MEDICAL_ID": ["PAT-61438"],
            "NATIONAL_ID": ["880719 5483 081"],
            "INSURANCE_ID": ["FH-1127643"],
            "PHONE": ["+27 79 334 5612"],
            "EMAIL": ["keegan@physiofitsa.co.za"],
            "ADDRESS": ["8 Jacaranda Crescent, Lonehill, 2062"],
        },
    },
    # ── New scenario 8 ───────────────────────────────────────────────────
    {
        "name": "Pediatric Vaccination",
        "instruction": "Schedule the child's vaccination appointment and update their immunisation record.",
        "input": (
            "Vaccination schedule for Liam van Wyk (DOB: 14 September 2024), "
            "patient ID: PAT-73290. Due for 18-month immunisations: DTaP-IPV-Hib booster, "
            "Hepatitis A 1st dose, and Varicella vaccine. "
            "Appointment with Dr. Priya Naidoo at Mediclinic Stellenbosch paediatric clinic. "
            "Parent/guardian: Elsabe van Wyk, cell +27 83 210 7744, "
            "email elsabe.vanwyk@outlook.co.za. "
            "Medical aid: Bestmed, member BM-4459021. SA ID of guardian: 920301 0812 089."
        ),
        "expected_tools": ["schedule_appointment", "update_patient_record"],
        "expected_args": {
            "schedule_appointment": {
                "patient_name": lambda v: "Liam" in str(v) or "PERSON" in str(v),
                "doctor": lambda v: "Naidoo" in str(v) or "Priya" in str(v) or "PERSON" in str(v),
                "reason": lambda v: "vaccin" in str(v).lower() or "immunis" in str(v).lower(),
            },
            "update_patient_record": {
                "patient_name": lambda v: "Liam" in str(v) or "PERSON" in str(v),
                "patient_id": lambda v: "PAT-73290" in str(v) or "MEDICAL_ID" in str(v) or "ID" in str(v),
                "diagnosis": lambda v: "vaccin" in str(v).lower() or "immunis" in str(v).lower(),
            },
        },
        "pii_entities": {
            "PERSON": ["Liam van Wyk", "Elsabe van Wyk", "Dr. Priya Naidoo"],
            "DATE_OF_BIRTH": ["14 September 2024"],
            "MEDICAL_ID": ["PAT-73290"],
            "NATIONAL_ID": ["920301 0812 089"],
            "INSURANCE_ID": ["BM-4459021"],
            "PHONE": ["+27 83 210 7744"],
            "EMAIL": ["elsabe.vanwyk@outlook.co.za"],
        },
    },
    # ── New scenario 9 ───────────────────────────────────────────────────
    {
        "name": "Mental Health Assessment",
        "instruction": "Update the patient's psychiatric record and order the required blood work for medication monitoring.",
        "input": (
            "Psychiatric evaluation for Zanele Khumalo (ID: PAT-40562), age 29. "
            "Diagnosis: Major Depressive Disorder, recurrent, moderate (F33.1). "
            "Patient reports persistent low mood, insomnia, and anhedonia for 6 weeks. "
            "PHQ-9 score: 17. Adjusting medication from Sertraline 50mg to 100mg daily, "
            "adding Mirtazapine 15mg nocte. Treating psychiatrist: Dr. Willem du Plessis, "
            "practice number PR-0067189. SA ID: 960528 0934 086. "
            "Order liver function tests and serum sodium to monitor medication safety. "
            "Patient email: z.khumalo@gmail.com. Phone: +27 71 882 3401. "
            "Medical aid: GEMS, member number GE-7723018."
        ),
        "expected_tools": ["update_patient_record", "order_lab_test"],
        "expected_args": {
            "update_patient_record": {
                "patient_name": lambda v: "Zanele" in str(v) or "PERSON" in str(v),
                "patient_id": lambda v: "PAT-40562" in str(v) or "MEDICAL_ID" in str(v) or "ID" in str(v),
                "diagnosis": lambda v: "depressi" in str(v).lower() or "F33" in str(v),
                "prescriptions": lambda v: isinstance(v, list) and len(v) >= 1,
            },
            "order_lab_test": {
                "patient_name": lambda v: "Zanele" in str(v) or "PERSON" in str(v),
                "ordering_physician": lambda v: "du Plessis" in str(v) or "Willem" in str(v) or "PERSON" in str(v),
            },
        },
        "pii_entities": {
            "PERSON": ["Zanele Khumalo", "Dr. Willem du Plessis"],
            "MEDICAL_ID": ["PAT-40562"],
            "NATIONAL_ID": ["960528 0934 086"],
            "INSURANCE_ID": ["GE-7723018"],
            "PHONE": ["+27 71 882 3401"],
            "EMAIL": ["z.khumalo@gmail.com"],
            "LICENCE_NUMBER": ["PR-0067189"],
        },
    },
    # ── New scenario 10 ──────────────────────────────────────────────────
    {
        "name": "Chronic Disease Management",
        "instruction": "Update the patient's record with the revised treatment plan and order monitoring labs.",
        "input": (
            "Annual chronic disease review for Ismail Jacobs (ID: PAT-33971), age 58. "
            "Comorbidities: Type 2 Diabetes Mellitus (E11.9) and Essential Hypertension (I10). "
            "Current regimen: Metformin 1000mg BD, Gliclazide 80mg daily, "
            "Enalapril 20mg daily, Hydrochlorothiazide 12.5mg daily. "
            "Latest BP: 148/92, random glucose: 11.4 mmol/L — suboptimal control. "
            "Plan: increase Enalapril to 20mg BD, add Empagliflozin 10mg daily. "
            "Attending physician: Dr. Nombulelo Sithole, HPCSA reg MP-0295814. "
            "SA ID: 670903 5312 080. Patient cell: +27 84 667 2190, "
            "email ismail.jacobs@vodamail.co.za. "
            "Medical aid: Sizwe Medical Fund, member SZ-6610483. "
            "Order HbA1c, renal function panel, fasting lipogram, and urine ACR."
        ),
        "expected_tools": ["update_patient_record", "order_lab_test"],
        "expected_args": {
            "update_patient_record": {
                "patient_name": lambda v: "Ismail" in str(v) or "Jacobs" in str(v) or "PERSON" in str(v),
                "patient_id": lambda v: "PAT-33971" in str(v) or "MEDICAL_ID" in str(v) or "ID" in str(v),
                "diagnosis": lambda v: "diabet" in str(v).lower() or "hypertension" in str(v).lower(),
                "prescriptions": lambda v: isinstance(v, list) and len(v) >= 3,
            },
            "order_lab_test": {
                "patient_name": lambda v: "Ismail" in str(v) or "Jacobs" in str(v) or "PERSON" in str(v),
                "ordering_physician": lambda v: "Sithole" in str(v) or "Nombulelo" in str(v) or "PERSON" in str(v),
            },
        },
        "pii_entities": {
            "PERSON": ["Ismail Jacobs", "Dr. Nombulelo Sithole"],
            "MEDICAL_ID": ["PAT-33971"],
            "NATIONAL_ID": ["670903 5312 080"],
            "INSURANCE_ID": ["SZ-6610483"],
            "PHONE": ["+27 84 667 2190"],
            "EMAIL": ["ismail.jacobs@vodamail.co.za"],
            "LICENCE_NUMBER": ["MP-0295814"],
        },
    },
    # ── New scenario 11 ──────────────────────────────────────────────────
    {
        "name": "Maternal Care",
        "instruction": "Schedule the prenatal visit and order the required blood work and ultrasound.",
        "input": (
            "Prenatal booking for Palesa Moabi (ID: PAT-82156), age 31, G2P1. "
            "Estimated gestational age: 12 weeks. LMP: 15 December 2025. "
            "Schedule first-trimester screening appointment with Dr. Riana Venter "
            "at Netcare Waterfall City Hospital, obstetrics unit. "
            "Order nuchal translucency ultrasound, full blood count, blood group and Rh, "
            "RPR, HIV screening, and rubella IgG. "
            "SA ID: 940611 0456 083. Medical aid: Medshield, member MS-3304877. "
            "Patient phone: +27 76 519 8830, email palesa.moabi@icloud.com. "
            "Emergency contact: husband Teboho Moabi, +27 82 440 3167."
        ),
        "expected_tools": ["schedule_appointment", "order_lab_test"],
        "expected_args": {
            "schedule_appointment": {
                "patient_name": lambda v: "Palesa" in str(v) or "PERSON" in str(v),
                "doctor": lambda v: "Venter" in str(v) or "Riana" in str(v) or "PERSON" in str(v),
                "reason": lambda v: "prenatal" in str(v).lower() or "screening" in str(v).lower() or "trimester" in str(v).lower(),
            },
            "order_lab_test": {
                "patient_name": lambda v: "Palesa" in str(v) or "PERSON" in str(v),
                "ordering_physician": lambda v: "Venter" in str(v) or "Riana" in str(v) or "PERSON" in str(v),
            },
        },
        "pii_entities": {
            "PERSON": ["Palesa Moabi", "Dr. Riana Venter", "Teboho Moabi"],
            "MEDICAL_ID": ["PAT-82156"],
            "NATIONAL_ID": ["940611 0456 083"],
            "INSURANCE_ID": ["MS-3304877"],
            "PHONE": ["+27 76 519 8830", "+27 82 440 3167"],
            "EMAIL": ["palesa.moabi@icloud.com"],
        },
    },
    # ── New scenario 12 ──────────────────────────────────────────────────
    {
        "name": "Discharge Planning",
        "instruction": "Update the patient's discharge record and send a referral for home-based care.",
        "input": (
            "Discharge summary for Grace Ndlovu (ID: PAT-19084), age 72. "
            "Admitted 25 February 2026 for community-acquired pneumonia (J18.9) "
            "with COPD exacerbation (J44.1). Treated with IV Augmentin and nebulised "
            "Salbutamol/Ipratropium. Stable for discharge on 7 March 2026. "
            "Discharge medications: Augmentin 625mg TDS x 5 days, Prednisone 30mg taper "
            "over 10 days, Spiriva 18mcg daily inhaler, Ventolin MDI PRN. "
            "Refer to Sr. Margaret Pillay at Healing Hands Home Care, "
            "email m.pillay@healinghandshc.co.za, for daily wound care and oxygen monitoring. "
            "Discharging physician: Dr. Andile Mkhize. SA ID: 530914 0782 087. "
            "Medical aid: Bonitas, member BO-5519832. "
            "Next-of-kin: daughter Noluthando Ndlovu, cell +27 63 921 4578. "
            "Patient phone: +27 72 305 8816."
        ),
        "expected_tools": ["update_patient_record", "send_referral"],
        "expected_args": {
            "update_patient_record": {
                "patient_name": lambda v: "Grace" in str(v) or "Ndlovu" in str(v) or "PERSON" in str(v),
                "patient_id": lambda v: "PAT-19084" in str(v) or "MEDICAL_ID" in str(v) or "ID" in str(v),
                "diagnosis": lambda v: "pneumonia" in str(v).lower() or "COPD" in str(v) or "J18" in str(v),
                "prescriptions": lambda v: isinstance(v, list) and len(v) >= 3,
            },
            "send_referral": {
                "patient_name": lambda v: "Grace" in str(v) or "Ndlovu" in str(v) or "PERSON" in str(v),
                "specialist": lambda v: "Pillay" in str(v) or "Margaret" in str(v) or "PERSON" in str(v),
                "specialist_email": lambda v: "pillay" in str(v) or "EMAIL" in str(v),
                "reason": lambda v: "home care" in str(v).lower() or "wound" in str(v).lower() or "discharge" in str(v).lower(),
            },
        },
        "pii_entities": {
            "PERSON": ["Grace Ndlovu", "Dr. Andile Mkhize", "Sr. Margaret Pillay", "Noluthando Ndlovu"],
            "MEDICAL_ID": ["PAT-19084"],
            "NATIONAL_ID": ["530914 0782 087"],
            "INSURANCE_ID": ["BO-5519832"],
            "PHONE": ["+27 63 921 4578", "+27 72 305 8816"],
            "EMAIL": ["m.pillay@healinghandshc.co.za"],
        },
    },
]
