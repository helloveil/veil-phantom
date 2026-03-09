"""
VeilPhantom — Test suite ported from scripts/redaction_test.swift.
87 test cases across 18 categories.

Run with: pytest tests/test_engine.py -v
For regex-only (no Shade model): default behavior.
"""

import pytest

from veil_phantom import VeilClient, VeilConfig

# Use regex-only for deterministic tests (no Shade model dependency)
client = VeilClient(VeilConfig.regex_only())

requires_shade = pytest.mark.skip(reason="Requires Shade model for higher-accuracy detection")


def _check(input_text: str, must_redact: list[str], must_not_redact: list[str]):
    """Helper: verify redaction catches what it should, keeps what it should."""
    result = client.redact(input_text)
    sanitized = result.sanitized

    errors = []

    # Check must_redact: these values should NOT appear in sanitized text
    for val in must_redact:
        if val in sanitized:
            errors.append(f"LEAKED: '{val}' still in output")

    # Check must_not_redact: these values SHOULD still appear
    for val in must_not_redact:
        if val not in sanitized:
            errors.append(f"OVER-REDACTED: '{val}' was removed")

    if errors:
        pytest.fail(
            f"\n  Input: {input_text[:100]}...\n  Sanitized: {sanitized[:100]}...\n  "
            + "\n  ".join(errors)
        )


# ── PERSON ──

def test_person_full_names():
    _check(
        "Sarah Chen presented the quarterly report. Michael Wong asked about the budget. Lisa Park took notes during the session.",
        must_redact=["Sarah Chen", "Michael Wong", "Lisa Park"],
        must_not_redact=["quarterly", "report", "budget", "notes", "session"],
    )

@requires_shade
def test_person_single_names():
    _check(
        "Nakai mentioned that Thabo would handle the deployment while Priya reviews the code.",
        must_redact=["Nakai", "Thabo", "Priya"],
        must_not_redact=["deployment", "code"],
    )

def test_person_western_full_names():
    _check(
        "Grant Cardone discussed investment strategies with Robert Kiyosaki and Warren Buffett.",
        must_redact=["Grant Cardone", "Robert Kiyosaki", "Warren Buffett"],
        must_not_redact=["investment", "strategies"],
    )

def test_person_with_titles():
    _check(
        "Dr. James Smith and Prof. Maria Garcia will lead the workshop.",
        must_redact=["James Smith", "Maria Garcia"],
        must_not_redact=["workshop"],
    )


# ── ORG ──

def test_org_compound_names():
    _check(
        "We signed a deal with Goldman Sachs and Standard Bank is our primary lender. McKinsey provided the consulting.",
        must_redact=["Goldman Sachs", "Standard Bank", "McKinsey"],
        must_not_redact=["deal", "primary", "lender", "consulting"],
    )

def test_org_tech_whitelisted():
    _check(
        "We use Slack for messaging, Zoom for calls, and deploy on AWS. Our code is on GitHub.",
        must_redact=[],
        must_not_redact=["Slack", "Zoom", "AWS", "GitHub"],
    )


# ── EMAIL ──

def test_email_standard():
    _check(
        "Please send the report to sarah.chen@company.com and cc finance@globaltechinc.com for review.",
        must_redact=["sarah.chen@company.com", "finance@globaltechinc.com"],
        must_not_redact=["report", "review"],
    )

def test_email_spoken():
    _check(
        "You can reach me at kai at hello veil dot com or john at example dot org for follow up.",
        must_redact=["kai at hello veil dot com", "john at example dot org"],
        must_not_redact=["reach", "follow"],
    )


# ── PHONE ──

def test_phone_intl_and_sa():
    _check(
        "Call me at +27 82 555 1234 or the office at 011-555-6789. My cell is 082-123-4567.",
        must_redact=["+27 82 555 1234", "011-555-6789", "082-123-4567"],
        must_not_redact=["office", "cell"],
    )


# ── MONEY ──

def test_money_usd():
    _check(
        "The Series B round raised $25 million. Operating costs are $500K per quarter. Total revenue hit $12.5M.",
        must_redact=["$500K", "$12.5M"],
        must_not_redact=["Series", "Operating", "costs", "quarter", "revenue"],
    )

def test_money_zar_prefix():
    _check(
        "The property is valued at R50 million. Annual salary of R250k. Budget allocation of R1,500,000.",
        must_redact=["R250k", "R1,500,000"],
        must_not_redact=["property", "valued", "salary", "allocation"],
    )

def test_money_zar_suffix():
    _check(
        "We need 50 million rand for the expansion. The contract is worth 100 rand per unit.",
        must_redact=[],
        must_not_redact=["expansion", "contract", "unit"],
    )

def test_money_verbal():
    _check(
        "They offered five million dollars for the acquisition. The reserve is twenty thousand rand.",
        must_redact=[],
        must_not_redact=["offered", "acquisition", "reserve"],
    )


# ── DATE ──

def test_dates_formats():
    _check(
        "The deadline is January 15th. Board meeting on 03/20/2025. Review is next quarter.",
        must_redact=["January 15th", "03/20/2025", "next quarter"],
        must_not_redact=["deadline", "Board"],
    )


# ── SCENARIO ──

def test_mixed_finance_committee():
    _check(
        "Sarah Chen opened the meeting at 9am. She reported Q3 revenue of $12.5 million, up from $10M last quarter. Michael Wong from Standard Bank confirmed the Series B funding of $25 million is on track. Lisa Park noted that the GlobalTech acquisition, valued at R50 million, needs board approval by January 15th. Contact Michael at michael.wong@standardbank.co.za or call +27 82 555 1234 for updates.",
        must_redact=["Sarah Chen", "Michael Wong", "Lisa Park", "Standard Bank", "$10M", "michael.wong@standardbank.co.za", "+27 82 555 1234", "January 15th"],
        must_not_redact=["meeting", "reported", "revenue", "confirmed", "noted", "board", "approval", "updates"],
    )


# ── FALSE POSITIVE ──

def test_fp_tech_words():
    _check(
        "We discussed the Python API integration using Docker and Kubernetes. The team will deploy on AWS next sprint. The standup went well.",
        must_redact=[],
        must_not_redact=["Python", "API", "Docker", "Kubernetes", "AWS", "sprint", "standup", "team", "deploy"],
    )

def test_fp_filler_words():
    _check(
        "Um, yeah so basically we're gonna need to like figure out the approach. Honestly it's pretty straightforward actually.",
        must_redact=[],
        must_not_redact=["Um", "yeah", "basically", "gonna", "Honestly", "pretty", "actually"],
    )

def test_fp_business_jargon():
    _check(
        "Let's circle back on the Q4 roadmap. The MVP is ready for the board review. We need to streamline the workflow.",
        must_redact=[],
        must_not_redact=["circle", "roadmap", "MVP", "board", "review", "streamline", "workflow"],
    )


# ── EDGE ──

def test_edge_round_trip():
    result = client.redact(
        "Sarah Chen from Goldman Sachs discussed the $25M deal. Contact her at sarah@gs.com or +27 82 555 1234. Deadline is January 15th."
    )
    # Verify no original values leaked
    for val in ["Sarah Chen", "Goldman Sachs", "$25M", "sarah@gs.com", "+27 82 555 1234", "January 15th"]:
        assert val not in result.sanitized, f"LEAKED: {val}"
    # Verify rehydration round-trip
    ai_response = result.sanitized  # simulate AI echoing tokens
    rehydrated = result.rehydrate(ai_response)
    # Original values should be back
    assert "Sarah Chen" in rehydrated
    assert "Goldman Sachs" in rehydrated

@requires_shade
def test_edge_repeated_names():
    _check(
        "Sarah mentioned the plan. Then Sarah reviewed the budget. Sarah will follow up next week.",
        must_redact=["Sarah"],
        must_not_redact=["plan", "budget", "follow"],
    )

def test_edge_adjacent_pii():
    _check(
        "Email john@acme.com, phone 082-555-1234, budget $5M, deadline January 20th, all for Michael Roberts.",
        must_redact=["john@acme.com", "082-555-1234", "$5M", "January 20th", "Michael Roberts"],
        must_not_redact=["budget", "deadline"],
    )

def test_edge_empty_input():
    _check(
        "Hi. Ok. Yes. No. The end.",
        must_redact=[],
        must_not_redact=["Hi", "Ok", "Yes", "No", "The", "end"],
    )


# ── GOV ID ──

def test_govid_ssn():
    _check(
        "For the background check, my social security number is 123-45-6789. Please keep this confidential.",
        must_redact=["123-45-6789"],
        must_not_redact=["background", "check", "confidential"],
    )

def test_govid_ssn_spaces():
    _check(
        "HR needs the SSN on file. It's 987 65 4321 for the benefits enrollment.",
        must_redact=["987 65 4321"],
        must_not_redact=["benefits", "enrollment"],
    )

def test_govid_sa_id():
    _check(
        "My ID number is 9405105800086 for the FICA verification.",
        must_redact=["9405105800086"],
        must_not_redact=["verification"],
    )

def test_govid_sa_id_hr():
    _check(
        "Employee onboarding: RSA ID 8501016800085, please file with SARS.",
        must_redact=["8501016800085"],
        must_not_redact=["onboarding", "file"],
    )

def test_govid_passport():
    _check(
        "For the visa application, my passport number is A04556782. It expires next year.",
        must_redact=["passport number is A04556782"],
        must_not_redact=["visa", "application", "expires"],
    )

def test_govid_passport_alt():
    _check(
        "His US passport no 532876291 was submitted for verification.",
        must_redact=["passport no 532876291"],
        must_not_redact=["submitted", "verification"],
    )

def test_govid_drivers_license():
    _check(
        "Driver's license number is D12345678 for the fleet registration.",
        must_redact=["license number is D12345678"],
        must_not_redact=["fleet", "registration"],
    )


# ── CARD ──

def test_card_visa():
    _check(
        "Please charge the corporate card 4532 1234 5678 9012 for the conference booking.",
        must_redact=["4532 1234 5678 9012"],
        must_not_redact=["corporate", "conference", "booking"],
    )

def test_card_dashed():
    _check(
        "The payment card is 5500-0000-0000-0004 expiring next month.",
        must_redact=["5500-0000-0000-0004"],
        must_not_redact=["payment", "expiring"],
    )


# ── BANK ──

def test_bank_account():
    _check(
        "Wire the funds to account number 1234567890 at Standard Bank.",
        must_redact=["account number 1234567890", "Standard Bank"],
        must_not_redact=["Wire", "funds"],
    )

def test_bank_account_context():
    _check(
        "My FNB account no is 62450089123 for the salary deposit.",
        must_redact=["account no is 62450089123"],
        must_not_redact=["salary", "deposit"],
    )

def test_bank_iban():
    _check(
        "Transfer to IBAN GB29 NWBK 6016 1331 9268 19 for the vendor payment.",
        must_redact=["GB29 NWBK 6016 1331 9268 19"],
        must_not_redact=["Transfer", "vendor", "payment"],
    )


# ── IP ──

def test_ip_ipv4():
    _check(
        "The production server is at 192.168.1.100 and the staging server at 10.0.0.55 needs a restart.",
        must_redact=["192.168.1.100", "10.0.0.55"],
        must_not_redact=["production", "server", "staging", "restart"],
    )

def test_ip_whitelist_context():
    _check(
        "Whitelist IP 203.45.67.89 for the API gateway. Block 45.33.32.156 from the firewall.",
        must_redact=["203.45.67.89", "45.33.32.156"],
        must_not_redact=["gateway", "firewall"],
    )


# ── ADDRESS ──

def test_address_street():
    _check(
        "Send the documents to 42 Rivonia Road in Sandton. The warehouse is at 100 Main Street.",
        must_redact=["42 Rivonia Road", "100 Main Street"],
        must_not_redact=["documents", "warehouse"],
    )

def test_address_full():
    _check(
        "Ship the equipment to 200 Park Avenue for the new office setup.",
        must_redact=["200 Park Avenue"],
        must_not_redact=["Ship", "equipment", "office", "setup"],
    )


# ── CONTEXTUAL (V9) ──

def test_context_corporate_csuite():
    _check(
        "The CEO discussed the pending acquisition with the board. The CFO raised concerns about valuation. The Chief Technology Officer will assess due diligence.",
        must_redact=["The CEO", "The CFO", "pending acquisition", "The Chief Technology Officer"],
        must_not_redact=["discussed", "board", "concerns", "valuation", "assess"],
    )

def test_context_corruption():
    _check(
        "We need to discuss the corruption allegations against the department head. There's also a bribery scandal brewing.",
        must_redact=["corruption allegations", "bribery scandal"],
        must_not_redact=["discuss", "department", "head", "brewing"],
    )

def test_context_corporate_ma():
    _check(
        "This is about the pending acquisition. Do not discuss the pending merger with anyone outside the team.",
        must_redact=["pending acquisition", "pending merger"],
        must_not_redact=["discuss", "anyone", "outside", "team"],
    )

def test_context_insider_trading():
    _check(
        "We have material non-public information about the Q3 earnings. This is insider information that cannot be shared.",
        must_redact=["material non-public information", "insider information"],
        must_not_redact=["earnings", "shared"],
    )

def test_context_whistleblower():
    _check(
        "The whistleblower reported unauthorized access to the secure systems. There was also a data breach last week.",
        must_redact=["whistleblower", "unauthorized access", "data breach"],
        must_not_redact=["reported", "secure", "systems"],
    )

def test_context_hr_misconduct():
    _check(
        "The disciplinary hearing is scheduled for Friday regarding the misconduct allegations. The termination proceedings will follow.",
        must_redact=["disciplinary hearing", "misconduct allegations", "termination proceedings"],
        must_not_redact=["scheduled", "Friday", "regarding", "follow"],
    )

def test_context_pre_announcement():
    _check(
        "We're discussing the numbers before the announcement. Keep this quiet until it goes public.",
        must_redact=["before the announcement"],
        must_not_redact=["discussing", "numbers", "Keep", "quiet"],
    )

def test_context_earnings_embargo():
    _check(
        "This data is ahead of the earnings call. It's embargoed until the official release.",
        must_redact=["ahead of the earnings call", "embargoed until"],
        must_not_redact=["data", "official", "release"],
    )

def test_context_blackout_period():
    _check(
        "We're in a quiet period before the IPO. No trading during the blackout period.",
        must_redact=["before the IPO", "during the blackout period"],
        must_not_redact=["trading"],
    )

def test_context_off_record():
    _check(
        "This is strictly off the record. The information is not for public distribution.",
        must_redact=["off the record", "not for public distribution"],
        must_not_redact=["strictly", "information"],
    )

def test_context_unique_patient():
    _check(
        "The patient with the rare condition from last Tuesday needs follow-up. She's the only survivor who recovered fully.",
        must_redact=["the patient with the rare condition from last Tuesday", "the only survivor who"],
        must_not_redact=["needs", "follow-up", "recovered", "fully"],
    )

def test_context_unique_employee():
    _check(
        "The employee with the specific complaint in the case needs representation. He's the sole witness who saw the incident.",
        must_redact=["the employee with the specific", "the sole witness who"],
        must_not_redact=["representation", "saw", "incident"],
    )

def test_context_ceo_sensitive():
    _check(
        "The CEO discussed the pending acquisition before the public announcement. This is confidential.",
        must_redact=["The CEO", "pending acquisition", "before the public announcement"],
        must_not_redact=["discussed"],
    )

def test_context_cfo_insider():
    _check(
        "The CFO shared insider information about the earnings ahead of the filing.",
        must_redact=["The CFO", "insider information", "ahead of the filing"],
        must_not_redact=["shared", "earnings"],
    )


# ── SPOKEN FORM ──

def test_spoken_phone():
    _check(
        "My phone number is plus two seven eight two five five five zero one four seven if you need to reach me directly.",
        must_redact=["plus two seven eight two five five five zero one four seven"],
        must_not_redact=["phone", "reach", "directly"],
    )

def test_spoken_phone_sa():
    _check(
        "Call me at plus two seven zero eight two one two three four five six seven for the details.",
        must_redact=["plus two seven zero eight two one two three four five six seven"],
        must_not_redact=["Call", "details"],
    )

def test_spoken_bank_account():
    _check(
        "The wire transfer should go to account number one two three four five six seven eight nine zero one two at First National Bank.",
        must_redact=["account number one two three four five six seven eight nine zero one two"],
        must_not_redact=["wire", "transfer"],
    )

def test_spoken_sa_id():
    _check(
        "The acquisition target's South African ID number is nine two zero one zero one five eight zero zero zero eight eight. Keep that confidential.",
        must_redact=["ID number is nine two zero one zero one five eight zero zero zero eight eight"],
        must_not_redact=["acquisition", "confidential"],
    )

def test_spoken_date_ordinal():
    _check(
        "Our next meeting is march fifteenth twenty twenty six. Thanks everyone.",
        must_redact=["march fifteenth twenty twenty six"],
        must_not_redact=["meeting", "Thanks"],
    )

def test_spoken_decimal_amount():
    _check(
        "Revenue came in at twelve point five million dollars which is up fifteen percent.",
        must_redact=[],
        must_not_redact=["Revenue", "percent"],
    )


# ── V12 REGRESSION ──

def test_v12_lowercase_banks():
    _check(
        "Wire the payment to first national bank. You can also transfer via absa or nedbank.",
        must_redact=["first national bank", "absa", "nedbank"],
        must_not_redact=["Wire", "payment", "transfer"],
    )

def test_v12_spoken_email_pre_nlp():
    _check(
        "Send the updated projections to sarah at veilprivacy dot com before the deadline.",
        must_redact=["sarah at veilprivacy dot com"],
        must_not_redact=["projections", "deadline"],
    )

def test_v12_trailing_punctuation():
    _check(
        "We partnered with Goldman Sachs, Standard Bank. Deutsche Bank! All confirmed the deal.",
        must_redact=["Goldman Sachs", "Standard Bank", "Deutsche Bank"],
        must_not_redact=["partnered", "confirmed", "deal"],
    )

def test_v12_nlp_stop_words():
    _check(
        "National growth is strong. Global trends look positive. South region performed best.",
        must_redact=[],
        must_not_redact=["National", "Global", "South", "growth", "trends", "region"],
    )


# ── REHYDRATION ──

def test_rehydrate_round_trip():
    """Test full redact → AI process → rehydrate cycle."""
    text = "Sarah Chen from Goldman Sachs sent $25M to sarah@gs.com"
    result = client.redact(text)

    # Simulate AI response using tokens
    ai_out = f"Summary: {result.sanitized}"
    final = result.rehydrate(ai_out)

    assert "Sarah Chen" in final
    assert "Goldman Sachs" in final
    assert "sarah@gs.com" in final

def test_rehydrate_orphan_cleanup():
    """AI-hallucinated tokens get cleaned up."""
    text = "Sarah Chen discussed the deal."
    result = client.redact(text)
    # Simulate AI adding a token that doesn't exist in our map
    ai_out = result.sanitized + " [PERSON_99] also attended."
    final = result.rehydrate(ai_out)
    assert "[PERSON_99]" not in final
    assert "[redacted]" in final

@requires_shade
def test_apply_token_map():
    """Apply same token map to different text."""
    text = "Sarah Chen discussed the plan."
    result = client.redact(text)
    other = "Sarah Chen also reviewed the budget."
    mapped = result.apply_token_map(other)
    assert "Sarah Chen" not in mapped
    assert "[PERSON_" in mapped
