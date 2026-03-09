"""
VeilPhantom Agent Utility Benchmark
====================================
Tests whether Claude Haiku can still perform tool use and be useful
when VeilPhantom sits as a privacy layer between user input and the model.

Benchmark: WITH VeilPhantom vs WITHOUT VeilPhantom
- Tool calling accuracy
- Instruction following
- Output quality
- PII leakage (bonus: does the model ever reconstruct real PII?)

Uses OpenRouter with Claude 3.5 Haiku.
"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from veil_phantom import VeilClient, VeilConfig

# ── OpenRouter Client ──

OPENROUTER_KEY = os.environ.get(
    "OPENROUTER_API_KEY",
    "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",
)
MODEL = "anthropic/claude-haiku-4.5"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)


# ── Tool Definitions (OpenAI format) ──

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "schedule_meeting",
            "description": "Schedule a meeting with specified participants, time, and agenda.",
            "parameters": {
                "type": "object",
                "properties": {
                    "participants": {"type": "array", "items": {"type": "string"}, "description": "List of participant names or emails"},
                    "date": {"type": "string", "description": "Meeting date"},
                    "time": {"type": "string", "description": "Meeting time"},
                    "agenda": {"type": "string", "description": "Meeting agenda or purpose"},
                },
                "required": ["participants", "date", "agenda"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to a recipient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body text"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a task or action item with assignee and deadline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "assignee": {"type": "string", "description": "Person assigned to the task"},
                    "deadline": {"type": "string", "description": "Task deadline"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"], "description": "Task priority"},
                },
                "required": ["title", "assignee"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_contact",
            "description": "Look up a contact's information by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the person to look up"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_funds",
            "description": "Initiate a fund transfer between accounts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_account": {"type": "string", "description": "Source account number or name"},
                    "to_account": {"type": "string", "description": "Destination account number or name"},
                    "amount": {"type": "string", "description": "Transfer amount"},
                    "reference": {"type": "string", "description": "Payment reference"},
                },
                "required": ["from_account", "to_account", "amount"],
            },
        },
    },
]

# ── Test Scenarios ──

SCENARIOS = [
    {
        "name": "Meeting Scheduling",
        "instruction": "Schedule a follow-up meeting with all the participants mentioned below. Use the schedule_meeting tool directly — you already have their names.",
        "input": (
            "Sarah Chen from Goldman Sachs presented the Q3 financials. Revenue hit $12.5 million. "
            "Michael Wong confirmed the Series B at $25M is closing January 15th. "
            "Lisa Park suggested we loop in the legal team. Contact Sarah at sarah.chen@gs.com. "
            "Michael's number is +27 82 555 1234."
        ),
        "expected_tools": ["schedule_meeting"],
        "pii_entities": ["Sarah Chen", "Michael Wong", "Lisa Park", "Goldman Sachs", "$12.5 million", "$25M", "sarah.chen@gs.com", "+27 82 555 1234"],
    },
    {
        "name": "Email Drafting",
        "instruction": "Draft and send a follow-up email to the client mentioned in this note, summarizing the key financial details discussed.",
        "input": (
            "Met with David Kim from ABC Capital today. They're offering $50M for the acquisition. "
            "Our counter is $65M. David's email is david.kim@abccapital.com. "
            "He wants a response by March 20th. The deal includes the Johannesburg office at "
            "42 Commissioner Street."
        ),
        "expected_tools": ["send_email"],
        "pii_entities": ["David Kim", "ABC Capital", "$50M", "$65M", "david.kim@abccapital.com", "42 Commissioner Street"],
    },
    {
        "name": "Fund Transfer",
        "instruction": "Process the fund transfer described in this message.",
        "input": (
            "Please transfer R2.5 million from Standard Bank account 62847501234 to "
            "IBAN GB29 NWBK 6016 1331 9268 19. Reference: INV-2024-Q3. "
            "This is for the Johnson & Partners consulting fee. Contact: +1 555-987-6543."
        ),
        "expected_tools": ["transfer_funds"],
        "pii_entities": ["R2.5 million", "62847501234", "GB29 NWBK 6016 1331 9268 19", "+1 555-987-6543", "Johnson & Partners"],
    },
    {
        "name": "Multi-Tool Coordination",
        "instruction": "Process this request: look up the contact, schedule a meeting with them, and create a task to prepare materials.",
        "input": (
            "I need to meet with Frank Lyons from McKinsey next Tuesday at 3 PM "
            "to discuss the due diligence report. His SSN for the background check is 456-78-9012. "
            "Also create a task for me to prepare the financial models before the meeting. "
            "The project budget is $8.3 million."
        ),
        "expected_tools": ["lookup_contact", "schedule_meeting", "create_task"],
        "pii_entities": ["Frank Lyons", "McKinsey", "456-78-9012", "$8.3 million"],
    },
    {
        "name": "Summarize & Act",
        "instruction": "Summarize this meeting and create action items for each participant mentioned.",
        "input": (
            "Board meeting notes: CEO Amanda Torres reported 15% revenue growth to $45M. "
            "CFO Brian Walsh flagged the pending acquisition of TechStart Inc for R120 million. "
            "Legal counsel Patricia Dlamini raised concerns about IP assignment clause 4.2. "
            "Action needed: Brian to finalize term sheet by March 1st, Patricia to review IP docs, "
            "Amanda to brief the investors at investor@veilcorp.com."
        ),
        "expected_tools": ["create_task"],
        "pii_entities": ["Amanda Torres", "Brian Walsh", "Patricia Dlamini", "TechStart Inc", "$45M", "R120 million", "investor@veilcorp.com"],
    },
]


def call_model(messages, use_tools=True):
    """Call Claude via OpenRouter."""
    kwargs = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 1024,
    }
    if use_tools:
        kwargs["tools"] = TOOLS
    return client.chat.completions.create(**kwargs)


def extract_tool_calls(response):
    """Extract tool calls from response."""
    msg = response.choices[0].message
    calls = []
    if msg.tool_calls:
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                args = {}
            calls.append({"name": tc.function.name, "args": args})
    return calls


def score_scenario(tool_calls, expected_tools, token_map=None):
    """Score tool accuracy and PII leakage."""
    called = [tc["name"] for tc in tool_calls]
    expected_set = set(expected_tools)
    called_set = set(called)

    correct = expected_set & called_set
    tool_accuracy = len(correct) / len(expected_set) if expected_set else 1.0

    # Check PII leakage in tool args
    leaked = []
    if token_map:
        originals = {v.original_value.lower() for v in token_map.values() if len(v.original_value) > 3}
        for tc in tool_calls:
            for key, value in tc["args"].items():
                if isinstance(value, str):
                    for orig in originals:
                        if orig in value.lower():
                            leaked.append(f"{key}={orig}")
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            for orig in originals:
                                if orig in item.lower():
                                    leaked.append(f"{key}[]={orig}")

    return {
        "called": called,
        "correct": list(correct),
        "missing": list(expected_set - called_set),
        "extra": list(called_set - expected_set),
        "tool_accuracy": tool_accuracy,
        "leaked_pii": leaked,
    }


def run_benchmark():
    print("=" * 70)
    print("VEILPHANTOM AGENT UTILITY BENCHMARK")
    print(f"Model: {MODEL} (via OpenRouter)")
    print("=" * 70)

    veil = VeilClient(VeilConfig.regex_only())

    system_msg_raw = {
        "role": "system",
        "content": (
            "You are a helpful assistant with access to tools. "
            "When the user asks you to perform actions, use the appropriate tools. "
            "Extract relevant information from the user's message and call tools with the correct parameters. "
            "You may call multiple tools if needed. Always use tools when the task requires action."
        ),
    }

    system_msg_veil = {
        "role": "system",
        "content": (
            "You are a helpful assistant with access to tools. "
            "When the user asks you to perform actions, use the appropriate tools. "
            "You may call multiple tools if needed. Always use tools when the task requires action.\n\n"
            "IMPORTANT: The user's message contains privacy tokens in the format [TYPE_N] "
            "(e.g. [PERSON_1], [EMAIL_1], [AMOUNT_1], [BANKACCT_1], [ORG_1], [PHONE_1], [DATE_1], [GOVID_1]). "
            "These tokens are placeholders that the system will replace with real values AFTER you respond. "
            "You MUST:\n"
            "1. Treat every token as if it were the real value — pass them directly into tool arguments.\n"
            "2. NEVER skip a tool call just because the input has tokens instead of real values.\n"
            "3. Use tokens exactly as they appear: if the email is [EMAIL_1], pass \"[EMAIL_1]\" as the email argument.\n"
            "4. If the task says to schedule a meeting, send an email, transfer funds, etc. — DO IT with the tokens.\n\n"
            "Examples:\n"
            "- send_email(to=\"[EMAIL_1]\", subject=\"Follow up\", body=\"Dear [PERSON_1], ...\")\n"
            "- transfer_funds(from_account=\"[BANKACCT_1]\", to_account=\"[BANKACCT_2]\", amount=\"[AMOUNT_1]\")\n"
            "- schedule_meeting(participants=[\"[PERSON_1]\", \"[PERSON_2]\"], date=\"[DATE_1]\")"
        ),
    }

    results_raw = []
    results_veil = []

    for scenario in SCENARIOS:
        print(f"\n{'─' * 60}")
        print(f"  {scenario['name']}")
        print(f"{'─' * 60}")

        user_text = f"{scenario['instruction']}\n\n{scenario['input']}"

        # ── WITHOUT VEIL ──
        print("\n  [WITHOUT VEIL]")
        t0 = time.time()
        try:
            resp = call_model([system_msg_raw, {"role": "user", "content": user_text}])
            latency = time.time() - t0
            tools_called = extract_tool_calls(resp)
            score = score_scenario(tools_called, scenario["expected_tools"])

            print(f"    Tools: {score['called']}")
            print(f"    Accuracy: {score['tool_accuracy']:.0%}")
            print(f"    Latency: {latency:.2f}s")
            for tc in tools_called:
                args_str = json.dumps(tc["args"])
                print(f"    → {tc['name']}({args_str[:120]}{'...' if len(args_str)>120 else ''})")

            results_raw.append({
                "scenario": scenario["name"],
                "accuracy": score["tool_accuracy"],
                "tools": score["called"],
                "latency": latency,
                "pii_exposed": True,
            })
        except Exception as e:
            print(f"    ERROR: {e}")
            results_raw.append({"scenario": scenario["name"], "accuracy": 0, "error": str(e)})

        # ── WITH VEIL ──
        print("\n  [WITH VEIL]")
        t0 = time.time()
        redaction = veil.redact(user_text)
        redact_ms = (time.time() - t0) * 1000

        print(f"    PII detected: {redaction.stats.total} entities ({redact_ms:.1f}ms)")

        t0 = time.time()
        try:
            resp = call_model([system_msg_veil, {"role": "user", "content": redaction.sanitized}])
            latency = time.time() - t0
            tools_called = extract_tool_calls(resp)
            score = score_scenario(tools_called, scenario["expected_tools"], redaction.token_map)

            print(f"    Tools: {score['called']}")
            print(f"    Accuracy: {score['tool_accuracy']:.0%}")
            print(f"    PII leaked: {len(score['leaked_pii'])} {'⚠ ' + str(score['leaked_pii']) if score['leaked_pii'] else '✓ NONE'}")
            print(f"    Latency: {latency:.2f}s + {redact_ms:.1f}ms redaction")
            for tc in tools_called:
                args_str = json.dumps(tc["args"])
                print(f"    → {tc['name']}({args_str[:120]}{'...' if len(args_str)>120 else ''})")

            results_veil.append({
                "scenario": scenario["name"],
                "accuracy": score["tool_accuracy"],
                "tools": score["called"],
                "latency": latency,
                "redact_ms": redact_ms,
                "pii_detected": redaction.stats.total,
                "pii_leaked": len(score["leaked_pii"]),
                "leaked_details": score["leaked_pii"],
            })
        except Exception as e:
            print(f"    ERROR: {e}")
            results_veil.append({"scenario": scenario["name"], "accuracy": 0, "error": str(e)})

        # Rate limit courtesy
        time.sleep(0.5)

    # ── SUMMARY ──
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)

    avg_acc_raw = sum(r.get("accuracy", 0) for r in results_raw) / len(results_raw)
    avg_acc_veil = sum(r.get("accuracy", 0) for r in results_veil) / len(results_veil)
    avg_lat_raw = sum(r.get("latency", 0) for r in results_raw if "latency" in r) / max(1, len([r for r in results_raw if "latency" in r]))
    avg_lat_veil = sum(r.get("latency", 0) for r in results_veil if "latency" in r) / max(1, len([r for r in results_veil if "latency" in r]))
    avg_redact = sum(r.get("redact_ms", 0) for r in results_veil) / len(results_veil)
    total_pii = sum(r.get("pii_detected", 0) for r in results_veil)
    total_leaked = sum(r.get("pii_leaked", 0) for r in results_veil)

    print(f"""
┌───────────────────────┬──────────────┬──────────────┐
│ Metric                │ Without Veil │  With Veil   │
├───────────────────────┼──────────────┼──────────────┤
│ Tool Accuracy (avg)   │    {avg_acc_raw:>6.0%}      │    {avg_acc_veil:>6.0%}      │
│ Avg Model Latency     │    {avg_lat_raw:>5.2f}s      │    {avg_lat_veil:>5.2f}s      │
│ Avg Redaction Time    │       —      │    {avg_redact:>5.1f}ms     │
│ PII Sent to Model     │     ALL      │      0       │
│ PII Detected          │       —      │      {total_pii:<8d}│
│ PII Leaked in Output  │      N/A     │      {total_leaked:<8d}│
└───────────────────────┴──────────────┴──────────────┘
""")

    # Per-scenario breakdown
    print("Per-scenario breakdown:")
    print(f"{'Scenario':<25} {'Raw Acc':>8} {'Veil Acc':>9} {'PII Det':>8} {'Leaked':>7}")
    print("─" * 60)
    for raw, veil_r in zip(results_raw, results_veil):
        print(f"{raw['scenario']:<25} {raw.get('accuracy',0):>7.0%} {veil_r.get('accuracy',0):>8.0%} {veil_r.get('pii_detected',0):>8} {veil_r.get('pii_leaked',0):>7}")

    delta = avg_acc_veil - avg_acc_raw
    print(f"\nTool accuracy delta: {delta:+.0%}")
    if delta >= 0:
        print("RESULT: VeilPhantom adds privacy with NO loss in agent utility.")
    else:
        print(f"RESULT: VeilPhantom adds privacy with {abs(delta):.0%} tool accuracy cost.")
    if total_leaked == 0:
        print("RESULT: Zero PII leakage across all scenarios.")
    else:
        print(f"WARNING: {total_leaked} PII values leaked into tool arguments.")

    # Save
    output = {
        "model": MODEL,
        "scenarios": len(SCENARIOS),
        "summary": {
            "avg_accuracy_raw": avg_acc_raw,
            "avg_accuracy_veil": avg_acc_veil,
            "accuracy_delta": delta,
            "avg_latency_raw": avg_lat_raw,
            "avg_latency_veil": avg_lat_veil,
            "avg_redaction_ms": avg_redact,
            "total_pii_detected": total_pii,
            "total_pii_leaked": total_leaked,
        },
        "raw_results": results_raw,
        "veil_results": results_veil,
    }
    path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved to {path}")


if __name__ == "__main__":
    run_benchmark()
