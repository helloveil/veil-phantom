"""
VeilPhantom — Agentic AI test setup.

Demonstrates VeilPhantom protecting PII in a multi-agent workflow.
No API keys needed — uses mock LLM responses.

Run: python examples/agentic_test.py
"""

from veil_phantom import VeilClient, VeilConfig

# ── Setup ──
veil = VeilClient(VeilConfig.regex_only())

print("=" * 70)
print("VEILPHANTOM — AGENTIC AI TEST HARNESS")
print("=" * 70)


# ── Test 1: Meeting transcript summarization ──
print("\n📋 TEST 1: Meeting Transcript → AI Summary")
print("-" * 50)

transcript = """
Sarah Chen from Goldman Sachs presented the Q3 financials.
Revenue hit $12.5 million, up 15% from last quarter.
Michael Wong confirmed the Series B at $25M is closing January 15th.
Contact: sarah.chen@gs.com, +27 82 555 1234.
The CFO flagged a pending acquisition worth R50 million.
Standard Bank is the lead underwriter.
"""

result = veil.redact(transcript)
print(f"Tokens detected: {result.stats.total}")
print(f"  Orgs: {result.stats.org} | Amounts: {result.stats.amount} | "
      f"Emails: {result.stats.email} | Phones: {result.stats.phone} | "
      f"Dates: {result.stats.date}")
print(f"\nSanitized (what the LLM sees):\n{result.sanitized}")

# Simulate LLM summarization
mock_summary = (
    f"Meeting summary: {list(result.token_map.keys())[0]} presented Q3 results "
    f"showing strong growth. The Series B funding is on track to close by "
    f"{result.sanitized.split('[DATE_1]')[0].split()[-1] if '[DATE_1]' in result.sanitized else 'scheduled date'}. "
    f"Key financial metrics were discussed."
)
rehydrated = result.rehydrate(mock_summary)
print(f"\nRehydrated AI output:\n{rehydrated}")


# ── Test 2: wrap() one-liner ──
print("\n\n📋 TEST 2: One-liner wrap()")
print("-" * 50)

def mock_llm(text: str) -> str:
    """Simulates an LLM that extracts action items."""
    return f"Action items from this meeting:\n1. Follow up on the funding discussion\n2. Review the {text[:50]}..."

output = veil.wrap(transcript, llm_fn=mock_llm)
print(f"Final output (PII restored):\n{output}")


# ── Test 3: Multi-turn agent conversation ──
print("\n\n📋 TEST 3: Multi-turn Agent Conversation")
print("-" * 50)

messages = [
    "Hi, I'm John Smith. My SSN is 123-45-6789 and email is john@acme.com.",
    "I need to transfer $50,000 from account 1234567890 to IBAN GB29 NWBK 6016 1331 9268 19.",
    "Please schedule this for March 15th. My phone is +1 555-123-4567.",
]

all_tokens = {}
for i, msg in enumerate(messages, 1):
    r = veil.redact(msg)
    all_tokens.update({k: v.original_value for k, v in r.token_map.items()})
    print(f"\nTurn {i}:")
    print(f"  User: {msg[:80]}...")
    print(f"  Safe: {r.sanitized[:80]}...")
    print(f"  PII caught: {r.stats.total} entities")

print(f"\nTotal unique PII tokens across conversation: {len(all_tokens)}")
for token, val in all_tokens.items():
    print(f"  {token} → {val}")


# ── Test 4: Sensitive context detection ──
print("\n\n📋 TEST 4: Contextual Sensitivity (Roles, Situations, Timing)")
print("-" * 50)

sensitive_texts = [
    "The CEO discussed the pending acquisition before the public announcement.",
    "The whistleblower reported unauthorized access to the database.",
    "Our CFO mentioned insider information ahead of earnings.",
    "The disciplinary hearing regarding misconduct allegations is Friday.",
]

for text in sensitive_texts:
    r = veil.redact(text)
    tokens = list(r.token_map.keys())
    print(f"  Input:  {text}")
    print(f"  Caught: {tokens}")
    print()


# ── Test 5: False positive resistance ──
print("\n📋 TEST 5: False Positive Resistance")
print("-" * 50)

safe_texts = [
    "We use Slack for messaging, Zoom for calls, and deploy on AWS.",
    "The Python API integration using Docker and Kubernetes went well.",
    "Let's circle back on the Q4 roadmap. The MVP is ready for board review.",
    "Um, yeah so basically we're gonna need to figure out the approach.",
]

all_clean = True
for text in safe_texts:
    r = veil.redact(text)
    status = "CLEAN" if r.stats.total == 0 else f"FALSE POSITIVE ({r.stats.total} tokens)"
    if r.stats.total > 0:
        all_clean = False
    print(f"  [{status}] {text[:70]}...")

print(f"\n  Result: {'ALL CLEAN' if all_clean else 'SOME FALSE POSITIVES'}")


# ── Summary ──
print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print("""
Note: Person names (Sarah Chen, Michael Wong, John Smith) are NOT caught
in regex-only mode. Install with Shade V7 model for full name detection:

    veil = VeilClient()  # auto-downloads Shade V7 from HuggingFace

With Shade V7 (PhoneticDeBERTa, 22M params, 97.12% F1), all person names,
orgs, and contextual PII are detected with <50ms latency.
Dual-pass inference + segment rescue for maximum accuracy.
""")
