"""Communications vertical — emails, meeting scheduling, memos."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "cc": {"type": "array", "items": {"type": "string"}},
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
                    "duration": {"type": "string"},
                    "agenda": {"type": "string"},
                    "location": {"type": "string"},
                },
                "required": ["participants", "date", "agenda"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create an action item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "assignee": {"type": "string"},
                    "deadline": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "description": {"type": "string"},
                },
                "required": ["title", "assignee"],
            },
        },
    },
]

SCENARIOS = [
    # ── Existing scenarios (1–3) ──────────────────────────────────────────
    {
        "name": "Meeting Follow-up",
        "instruction": "Send a follow-up email and create action items from this meeting transcript.",
        "input": (
            "Board meeting with CEO Amanda Torres, CFO Brian Walsh, and CTO Lisa Park. "
            "Key decisions: 1) Approve $45M Series C at $200M valuation. "
            "2) Brian to finalize term sheet by March 15th. "
            "3) Lisa to complete security audit before investor demo. "
            "Send summary to all three. Amanda: a.torres@company.com, "
            "Brian: b.walsh@company.com, Lisa: l.park@company.com."
        ),
        "expected_tools": ["send_email", "create_task"],
        "expected_args": {
            "send_email": {
                "to": lambda v: "a.torres@company.com" in v or "[EMAIL_" in v,
                "body": lambda v: (
                    ("Amanda Torres" in v or "[PERSON_" in v)
                    and ("$45M" in v or "[AMOUNT_" in v)
                ),
            },
            "create_task": {
                "assignee": lambda v: (
                    any(name in v for name in ("Brian Walsh", "Lisa Park"))
                    or "[PERSON_" in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": ["Amanda Torres", "Brian Walsh", "Lisa Park"],
            "AMOUNT": ["$45M", "$200M"],
            "EMAIL": ["a.torres@company.com", "b.walsh@company.com", "l.park@company.com"],
        },
    },
    {
        "name": "Client Meeting Setup",
        "instruction": "Schedule this meeting and send a confirmation email to the client.",
        "input": (
            "Need to set up a demo with Ravi Krishnan from Infosys. He's available Thursday at "
            "2 PM SAST. His team (Priya Nair and Amit Shah) should also attend. "
            "Location: Sandton City office, 5th floor boardroom. "
            "Ravi's email: ravi.krishnan@infosys.com. Confirm the meeting and send agenda."
        ),
        "expected_tools": ["schedule_meeting", "send_email"],
        "expected_args": {
            "schedule_meeting": {
                "participants": lambda v: (
                    any(name in str(v) for name in ("Ravi Krishnan", "Priya Nair", "Amit Shah"))
                    or "[PERSON_" in str(v)
                ),
                "location": lambda v: "Sandton City" in v or "[LOCATION_" in v,
            },
            "send_email": {
                "to": lambda v: "ravi.krishnan@infosys.com" in v or "[EMAIL_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Ravi Krishnan", "Priya Nair", "Amit Shah"],
            "ORG": ["Infosys"],
            "EMAIL": ["ravi.krishnan@infosys.com"],
            "LOCATION": ["Sandton City"],
        },
    },
    {
        "name": "Urgent Memo",
        "instruction": "Send an urgent internal email based on this situation.",
        "input": (
            "Security incident: unauthorized access detected on server prod-db-03 at 03:45 AM. "
            "IP address 192.168.1.105 attempted to access customer database containing "
            "450,000 records. CISO Daniel Botha needs to be notified immediately at "
            "d.botha@company.co.za. Also notify the DPO at dpo@company.co.za. "
            "Incident reference: SEC-2026-0042."
        ),
        "expected_tools": ["send_email"],
        "expected_args": {
            "send_email": {
                "to": lambda v: "d.botha@company.co.za" in v or "[EMAIL_" in v,
                "body": lambda v: (
                    ("Daniel Botha" in v or "[PERSON_" in v)
                    and ("192.168.1.105" in v or "[IP_ADDRESS_" in v)
                ),
            },
        },
        "pii_entities": {
            "PERSON": ["Daniel Botha"],
            "EMAIL": ["d.botha@company.co.za", "dpo@company.co.za"],
            "IP_ADDRESS": ["192.168.1.105"],
        },
    },
    # ── New scenarios (4–6) ───────────────────────────────────────────────
    {
        "name": "Vendor Negotiation",
        "instruction": "Draft an email to the vendor about contract renewal terms and create a follow-up task.",
        "input": (
            "We need to renegotiate our SaaS contract with Nexora Technologies. "
            "Current annual spend is $1.2M, renewal quote came in at $1.8M — "
            "a 50% increase we can't accept. Our procurement lead, Sandra Cheng "
            "(s.cheng@acme-corp.com), has been in talks with their account manager "
            "Yusuf Al-Rashidi (yusuf.alrashidi@nexora.io). "
            "Send Yusuf an email proposing a 3-year lock-in at $1.35M/year, "
            "emphasizing our 7-year relationship and volume commitment. "
            "Create a task for Sandra to prepare the counter-proposal deck by April 3rd, "
            "priority high."
        ),
        "expected_tools": ["send_email", "create_task"],
        "expected_args": {
            "send_email": {
                "to": lambda v: "yusuf.alrashidi@nexora.io" in v or "[EMAIL_" in v,
                "body": lambda v: (
                    ("$1.35M" in v or "[AMOUNT_" in v)
                    and ("Nexora" in v or "nexora" in v or "[ORG_" in v)
                ),
            },
            "create_task": {
                "assignee": lambda v: "Sandra Cheng" in v or "[PERSON_" in v,
                "deadline": lambda v: "April 3" in v or "2026-04-03" in v or "[DATE_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Sandra Cheng", "Yusuf Al-Rashidi"],
            "ORG": ["Nexora Technologies", "Acme Corp"],
            "EMAIL": ["s.cheng@acme-corp.com", "yusuf.alrashidi@nexora.io"],
            "AMOUNT": ["$1.2M", "$1.8M", "$1.35M"],
            "DATE": ["April 3rd"],
        },
    },
    {
        "name": "Team Standup",
        "instruction": "Schedule a recurring daily standup meeting for the distributed team.",
        "input": (
            "Set up a daily standup for the Platform Engineering squad. Members: "
            "Tomoko Hayashi (Tokyo, UTC+9), Keegan Daniels (Cape Town, UTC+2), "
            "and Mariana Oliveira (São Paulo, UTC-3). "
            "Find a 15-minute slot that works across all three timezones — "
            "suggest 09:00 AM UTC so nobody is outside business hours. "
            "The meeting should start Monday March 16th and recur weekdays. "
            "Agenda: blockers, progress on Project Aurora, and sprint health. "
            "Use the virtual room https://meet.company.com/platform-standup."
        ),
        "expected_tools": ["schedule_meeting"],
        "expected_args": {
            "schedule_meeting": {
                "participants": lambda v: (
                    any(name in str(v) for name in ("Tomoko Hayashi", "Keegan Daniels", "Mariana Oliveira"))
                    or "[PERSON_" in str(v)
                ),
                "agenda": lambda v: (
                    "blocker" in v.lower()
                    or "Aurora" in v
                    or "[PROJECT_" in v
                ),
                "location": lambda v: (
                    "meet.company.com" in v or "[URL_" in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": ["Tomoko Hayashi", "Keegan Daniels", "Mariana Oliveira"],
            "LOCATION": ["Tokyo", "Cape Town", "São Paulo"],
            "URL": ["https://meet.company.com/platform-standup"],
            "DATE": ["March 16th"],
        },
    },
    {
        "name": "Board Report",
        "instruction": "Email the quarterly board report and create a task to finalize the appendix.",
        "input": (
            "Send the Q4 2025 board report to chairperson Helen Vogt (h.vogt@boardmail.org) "
            "and non-executive director Kwame Asante (k.asante@boardmail.org). "
            "CC the CFO, Derek Zimmerman (d.zimmerman@truvex.com). "
            "Key financials: revenue $38.7M (up 14% YoY), EBITDA $9.2M, "
            "net cash position $22.4M. Headcount grew from 312 to 347. "
            "Customer NPS rose to 72. SSN on file for compliance: 418-63-7290 (Helen). "
            "Create a high-priority task for Derek to finalize the financial appendix "
            "and auditor sign-off by March 28th."
        ),
        "expected_tools": ["send_email", "create_task"],
        "expected_args": {
            "send_email": {
                "to": lambda v: "h.vogt@boardmail.org" in v or "[EMAIL_" in v,
                "cc": lambda v: (
                    "d.zimmerman@truvex.com" in str(v) or "[EMAIL_" in str(v)
                ),
                "body": lambda v: (
                    ("$38.7M" in v or "[AMOUNT_" in v)
                    and ("Helen Vogt" in v or "[PERSON_" in v)
                ),
            },
            "create_task": {
                "assignee": lambda v: "Derek Zimmerman" in v or "[PERSON_" in v,
                "priority": lambda v: v == "high",
            },
        },
        "pii_entities": {
            "PERSON": ["Helen Vogt", "Kwame Asante", "Derek Zimmerman"],
            "EMAIL": ["h.vogt@boardmail.org", "k.asante@boardmail.org", "d.zimmerman@truvex.com"],
            "AMOUNT": ["$38.7M", "$9.2M", "$22.4M"],
            "SSN": ["418-63-7290"],
            "ORG": ["Truvex"],
            "DATE": ["March 28th"],
        },
    },
    # ── Additional scenarios (7–12) ────────────────────────────────────────
    {
        "name": "Partnership Announcement",
        "instruction": "Send an announcement email about our new strategic partnership and create a follow-up task.",
        "input": (
            "We just signed a strategic partnership with Helios Dynamics, a leading "
            "AI infrastructure provider based in Berlin. Our VP of Business Development, "
            "Carla Mendes (c.mendes@optera.io), finalized the deal with their CEO, "
            "Florian Berger (f.berger@helios-dynamics.de). The partnership is worth "
            "$28M over 5 years and includes joint R&D, co-marketing, and shared patent "
            "licensing. Send the internal announcement email to the leadership distribution "
            "list at leadership@optera.io, CC Carla. Highlight the $28M deal value, "
            "Helios Dynamics as the partner, and the three pillars (R&D, co-marketing, "
            "patent licensing). Create a high-priority task for Carla to draft the external "
            "press release by March 20th."
        ),
        "expected_tools": ["send_email", "create_task"],
        "expected_args": {
            "send_email": {
                "to": lambda v: "leadership@optera.io" in v or "[EMAIL_" in v,
                "body": lambda v: (
                    ("$28M" in v or "[AMOUNT_" in v)
                    and ("Helios Dynamics" in v or "[ORG_" in v)
                ),
            },
            "create_task": {
                "assignee": lambda v: "Carla Mendes" in v or "[PERSON_" in v,
                "deadline": lambda v: "March 20" in v or "2026-03-20" in v or "[DATE_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Carla Mendes", "Florian Berger"],
            "ORG": ["Helios Dynamics", "Optera"],
            "EMAIL": ["c.mendes@optera.io", "f.berger@helios-dynamics.de", "leadership@optera.io"],
            "AMOUNT": ["$28M"],
            "DATE": ["March 20th"],
            "LOCATION": ["Berlin"],
        },
    },
    {
        "name": "Sprint Planning",
        "instruction": "Schedule a sprint planning meeting for the development team.",
        "input": (
            "Set up Sprint 14 planning for the Falcon team. Attendees: tech lead "
            "Raj Patel (raj.patel@crestware.dev), senior engineers Ines Moreau "
            "(ines.moreau@crestware.dev) and Oluwaseun Adeyemi (o.adeyemi@crestware.dev), "
            "and product owner Nadia Kowalski (n.kowalski@crestware.dev). "
            "Schedule for Tuesday March 17th at 10:00 AM EST, 2-hour block. "
            "Agenda: review Sprint 13 velocity (completed 34 of 40 story points), "
            "groom the backlog for Project Condor, and assign ownership of the "
            "authentication refactor epic. Use room https://zoom.us/j/9384756120."
        ),
        "expected_tools": ["schedule_meeting"],
        "expected_args": {
            "schedule_meeting": {
                "participants": lambda v: (
                    any(name in str(v) for name in ("Raj Patel", "Ines Moreau", "Oluwaseun Adeyemi", "Nadia Kowalski"))
                    or "[PERSON_" in str(v)
                ),
                "date": lambda v: "March 17" in v or "2026-03-17" in v or "[DATE_" in v,
                "agenda": lambda v: (
                    "Sprint 13" in v or "velocity" in v.lower()
                    or "Condor" in v or "[PROJECT_" in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": ["Raj Patel", "Ines Moreau", "Oluwaseun Adeyemi", "Nadia Kowalski"],
            "ORG": ["Crestware"],
            "EMAIL": [
                "raj.patel@crestware.dev",
                "ines.moreau@crestware.dev",
                "o.adeyemi@crestware.dev",
                "n.kowalski@crestware.dev",
            ],
            "URL": ["https://zoom.us/j/9384756120"],
            "DATE": ["March 17th"],
        },
    },
    {
        "name": "Customer Success Check-in",
        "instruction": "Send a check-in email to the customer and schedule a QBR meeting.",
        "input": (
            "Time for our quarterly business review with Luminos Healthcare. Their VP of "
            "Operations, Dr. Beatrice Okonkwo (b.okonkwo@luminoshc.com), has been our "
            "primary contact. Their contract renews in June at $750K ARR. "
            "Send Beatrice an email summarizing our last quarter: 99.97% uptime, 12 feature "
            "requests delivered, and CSAT score of 4.8/5. Mention that their dedicated CSM, "
            "Ethan Gallagher (e.gallagher@ourplatform.com), will host the QBR. "
            "Schedule the QBR for Friday March 27th at 1:00 PM GMT, 90 minutes, "
            "at their London office, 45 Queen Victoria Street. Include Beatrice, Ethan, "
            "and their CTO, Amir Haddad (a.haddad@luminoshc.com)."
        ),
        "expected_tools": ["send_email", "schedule_meeting"],
        "expected_args": {
            "send_email": {
                "to": lambda v: "b.okonkwo@luminoshc.com" in v or "[EMAIL_" in v,
                "body": lambda v: (
                    ("99.97%" in v or "uptime" in v.lower())
                    and ("Beatrice Okonkwo" in v or "Dr. Beatrice" in v or "[PERSON_" in v)
                ),
            },
            "schedule_meeting": {
                "participants": lambda v: (
                    any(name in str(v) for name in ("Beatrice Okonkwo", "Ethan Gallagher", "Amir Haddad"))
                    or "[PERSON_" in str(v)
                ),
                "date": lambda v: "March 27" in v or "2026-03-27" in v or "[DATE_" in v,
                "location": lambda v: "Queen Victoria" in v or "[LOCATION_" in v,
            },
        },
        "pii_entities": {
            "PERSON": ["Beatrice Okonkwo", "Ethan Gallagher", "Amir Haddad"],
            "ORG": ["Luminos Healthcare"],
            "EMAIL": ["b.okonkwo@luminoshc.com", "e.gallagher@ourplatform.com", "a.haddad@luminoshc.com"],
            "AMOUNT": ["$750K"],
            "LOCATION": ["London", "45 Queen Victoria Street"],
            "DATE": ["March 27th"],
        },
    },
    {
        "name": "All-Hands Prep",
        "instruction": "Schedule the company all-hands meeting and create preparation tasks.",
        "input": (
            "Our quarterly all-hands is coming up. Schedule it for Wednesday April 1st at "
            "4:00 PM UTC, 1 hour. Attendees: CEO Jun Tanaka (j.tanaka@veridian.co), "
            "COO Fatima El-Amin (f.elamin@veridian.co), and VP People, Lena Johansson "
            "(l.johansson@veridian.co). Use the virtual auditorium at "
            "https://stream.veridian.co/allhands. Agenda: Q1 results ($52M revenue, "
            "18% growth), product roadmap preview, and new office openings in Austin "
            "and Dublin. Create a medium-priority task for Fatima to compile the operational "
            "metrics deck by March 28th. Create a high-priority task for Lena to finalize "
            "the employee engagement survey results by March 26th."
        ),
        "expected_tools": ["schedule_meeting", "create_task"],
        "expected_args": {
            "schedule_meeting": {
                "participants": lambda v: (
                    any(name in str(v) for name in ("Jun Tanaka", "Fatima El-Amin", "Lena Johansson"))
                    or "[PERSON_" in str(v)
                ),
                "date": lambda v: "April 1" in v or "2026-04-01" in v or "[DATE_" in v,
                "agenda": lambda v: (
                    ("$52M" in v or "[AMOUNT_" in v)
                    or ("roadmap" in v.lower())
                ),
            },
            "create_task": {
                "assignee": lambda v: (
                    any(name in v for name in ("Fatima El-Amin", "Lena Johansson"))
                    or "[PERSON_" in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": ["Jun Tanaka", "Fatima El-Amin", "Lena Johansson"],
            "ORG": ["Veridian"],
            "EMAIL": ["j.tanaka@veridian.co", "f.elamin@veridian.co", "l.johansson@veridian.co"],
            "AMOUNT": ["$52M"],
            "URL": ["https://stream.veridian.co/allhands"],
            "LOCATION": ["Austin", "Dublin"],
            "DATE": ["April 1st", "March 28th", "March 26th"],
        },
    },
    {
        "name": "Investor Email",
        "instruction": "Send the monthly investor update email.",
        "input": (
            "Draft and send the February 2026 investor update to our lead investor, "
            "Gabriela Ruiz (g.ruiz@montecapital.com), at Monte Capital. CC board observer "
            "Dimitri Volkov (d.volkov@montecapital.com). Key metrics: MRR hit $4.1M "
            "(up from $3.6M in January), burn rate decreased to $1.9M/month, runway "
            "extended to 19 months. We closed 3 enterprise deals worth a combined $2.8M TCV "
            "including a landmark deal with Petrov Industries. Headcount is 214. "
            "Gabriela's SSN for wire compliance: 531-78-4629. "
            "Mention we are targeting $5M MRR by end of Q2."
        ),
        "expected_tools": ["send_email"],
        "expected_args": {
            "send_email": {
                "to": lambda v: "g.ruiz@montecapital.com" in v or "[EMAIL_" in v,
                "cc": lambda v: (
                    "d.volkov@montecapital.com" in str(v) or "[EMAIL_" in str(v)
                ),
                "body": lambda v: (
                    ("$4.1M" in v or "[AMOUNT_" in v)
                    and ("Gabriela Ruiz" in v or "[PERSON_" in v)
                ),
            },
        },
        "pii_entities": {
            "PERSON": ["Gabriela Ruiz", "Dimitri Volkov"],
            "ORG": ["Monte Capital", "Petrov Industries"],
            "EMAIL": ["g.ruiz@montecapital.com", "d.volkov@montecapital.com"],
            "AMOUNT": ["$4.1M", "$3.6M", "$1.9M", "$2.8M", "$5M"],
            "SSN": ["531-78-4629"],
        },
    },
    {
        "name": "Cross-Team Sync",
        "instruction": "Schedule a sync meeting between engineering and sales, and create alignment tasks.",
        "input": (
            "We need a cross-functional sync between Engineering and Sales to address "
            "the product feedback loop. Engineering lead: Mikhail Sorokin "
            "(m.sorokin@atlasbuild.io). Sales lead: Charlotte Dubois "
            "(c.dubois@atlasbuild.io). Also include solutions architect Wei Chen "
            "(w.chen@atlasbuild.io). Schedule for Thursday March 19th at 3:00 PM CET, "
            "1 hour, in Conference Room B at the Zurich HQ (Bahnhofstrasse 42). "
            "Agenda: top 10 feature requests from Q4 pipeline ($18M in influenced ARR), "
            "API versioning strategy, and enterprise onboarding friction points. "
            "Create a medium-priority task for Wei Chen to prepare the technical feasibility "
            "matrix by March 17th. Create a high-priority task for Charlotte to consolidate "
            "the top deal-blocker features list by March 16th."
        ),
        "expected_tools": ["schedule_meeting", "create_task"],
        "expected_args": {
            "schedule_meeting": {
                "participants": lambda v: (
                    any(name in str(v) for name in ("Mikhail Sorokin", "Charlotte Dubois", "Wei Chen"))
                    or "[PERSON_" in str(v)
                ),
                "date": lambda v: "March 19" in v or "2026-03-19" in v or "[DATE_" in v,
                "location": lambda v: "Bahnhofstrasse" in v or "Zurich" in v or "[LOCATION_" in v,
            },
            "create_task": {
                "assignee": lambda v: (
                    any(name in v for name in ("Wei Chen", "Charlotte Dubois"))
                    or "[PERSON_" in v
                ),
            },
        },
        "pii_entities": {
            "PERSON": ["Mikhail Sorokin", "Charlotte Dubois", "Wei Chen"],
            "ORG": ["Atlas Build"],
            "EMAIL": ["m.sorokin@atlasbuild.io", "c.dubois@atlasbuild.io", "w.chen@atlasbuild.io"],
            "AMOUNT": ["$18M"],
            "LOCATION": ["Zurich", "Bahnhofstrasse 42"],
            "DATE": ["March 19th", "March 17th", "March 16th"],
        },
    },
]
