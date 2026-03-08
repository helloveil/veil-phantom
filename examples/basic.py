"""
VeilPhantom — Basic usage example.

Run: python examples/basic.py
"""

from veil_phantom import VeilClient, VeilConfig

# Regex-only mode (no Shade model needed)
veil = VeilClient(VeilConfig.regex_only())

# Example: meeting transcript with PII
transcript = """
Sarah Chen from Goldman Sachs discussed the $25M acquisition deal.
Contact her at sarah.chen@gs.com or +27 82 555 1234.
The board meeting is January 15th. Michael Wong from Standard Bank confirmed.
"""

# Redact PII
result = veil.redact(transcript)

print("=" * 60)
print("ORIGINAL:")
print(transcript)
print("=" * 60)
print("SANITIZED (send this to your LLM):")
print(result.sanitized)
print("=" * 60)
print(f"Detected {result.stats.total} PII entities:")
print(f"  Persons: {result.stats.person}")
print(f"  Orgs:    {result.stats.org}")
print(f"  Amounts: {result.stats.amount}")
print(f"  Emails:  {result.stats.email}")
print(f"  Phones:  {result.stats.phone}")
print(f"  Dates:   {result.stats.date}")
print()
print("Token Map:")
for token, info in result.token_map.items():
    print(f"  {token} → '{info.original_value}' ({info.source.value})")

# Simulate AI response
print()
print("=" * 60)
ai_response = f"In this meeting, {list(result.token_map.keys())[0]} presented the financial update."
print(f"AI Response (with tokens): {ai_response}")
print(f"Rehydrated:                {result.rehydrate(ai_response)}")


# Example: wrap an LLM call
print()
print("=" * 60)
print("WRAP EXAMPLE:")
def fake_llm(text: str) -> str:
    """Simulate an LLM that echoes back the sanitized input."""
    return f"Summary: {text[:100]}..."

output = veil.wrap(transcript, llm_fn=fake_llm)
print(f"Final output (original values restored):\n{output}")
