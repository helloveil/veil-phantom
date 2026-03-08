#!/usr/bin/env python3
"""
VeilPhantom Comprehensive Benchmark Suite
==========================================
Tests agent utility across 8 verticals with VeilPhantom as middleware.
Each vertical has domain-specific tools, PII-heavy scenarios, and scoring.

Usage:
    export OPENROUTER_API_KEY=sk-or-v1-...
    python benchmarks/run_benchmarks.py [--vertical healthcare] [--model anthropic/claude-3.5-haiku]
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from veil_phantom import VeilClient, VeilConfig

# ── Verticals ──

from verticals.financial import TOOLS as FIN_TOOLS, SCENARIOS as FIN_SCENARIOS
from verticals.healthcare import TOOLS as HC_TOOLS, SCENARIOS as HC_SCENARIOS
from verticals.legal import TOOLS as LEG_TOOLS, SCENARIOS as LEG_SCENARIOS
from verticals.hr import TOOLS as HR_TOOLS, SCENARIOS as HR_SCENARIOS
from verticals.sales import TOOLS as SALES_TOOLS, SCENARIOS as SALES_SCENARIOS
from verticals.support import TOOLS as SUP_TOOLS, SCENARIOS as SUP_SCENARIOS
from verticals.communications import TOOLS as COMM_TOOLS, SCENARIOS as COMM_SCENARIOS
from verticals.multi_step import TOOLS as MULTI_TOOLS, SCENARIOS as MULTI_SCENARIOS

VERTICALS = {
    "financial": {"tools": FIN_TOOLS, "scenarios": FIN_SCENARIOS},
    "healthcare": {"tools": HC_TOOLS, "scenarios": HC_SCENARIOS},
    "legal": {"tools": LEG_TOOLS, "scenarios": LEG_SCENARIOS},
    "hr": {"tools": HR_TOOLS, "scenarios": HR_SCENARIOS},
    "sales": {"tools": SALES_TOOLS, "scenarios": SALES_SCENARIOS},
    "support": {"tools": SUP_TOOLS, "scenarios": SUP_SCENARIOS},
    "communications": {"tools": COMM_TOOLS, "scenarios": COMM_SCENARIOS},
    "multi_step": {"tools": MULTI_TOOLS, "scenarios": MULTI_SCENARIOS},
}

# ── Config ──

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools. "
    "When the user asks you to perform actions, use the appropriate tools. "
    "Extract relevant information from the user's message and call tools with correct parameters. "
    "You may call multiple tools if needed."
)

SYSTEM_PROMPT_VEIL = (
    "You are a helpful assistant with access to tools. "
    "When the user asks you to perform actions, use the appropriate tools. "
    "The input may contain privacy tokens like [PERSON_1], [EMAIL_1], [MONEY_1], etc. "
    "These are placeholders for real values. USE THESE TOKENS AS-IS in your tool call arguments — "
    "do NOT try to guess or reconstruct the real values. The system will replace tokens with "
    "real values after your response. Treat tokens exactly like real values."
)


@dataclass
class ScenarioResult:
    scenario: str
    vertical: str
    mode: str  # "raw" or "veil"
    accuracy: float = 0.0
    tools_called: list = field(default_factory=list)
    tools_expected: list = field(default_factory=list)
    tools_missing: list = field(default_factory=list)
    tools_extra: list = field(default_factory=list)
    latency: float = 0.0
    redact_ms: float = 0.0
    pii_detected: int = 0
    pii_leaked: int = 0
    leaked_details: list = field(default_factory=list)
    error: str = ""
    args_quality: float = 0.0  # 0-1 how well args match expected


def call_model(client, model, messages, tools):
    return client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        max_tokens=1024,
    )


def extract_tool_calls(response):
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


def check_pii_leakage(tool_calls, token_map):
    """Check if any original PII values appear in tool call arguments."""
    leaked = []
    if not token_map:
        return leaked
    originals = {v.original_value.lower() for v in token_map.values() if len(v.original_value) > 3}
    for tc in tool_calls:
        for key, value in tc["args"].items():
            values_to_check = []
            if isinstance(value, str):
                values_to_check.append(value)
            elif isinstance(value, list):
                values_to_check.extend(str(v) for v in value)
            elif isinstance(value, dict):
                values_to_check.extend(str(v) for v in value.values())
            for val in values_to_check:
                for orig in originals:
                    if orig in val.lower():
                        leaked.append(f"{tc['name']}.{key}={orig}")
    return leaked


def score_args_quality(tool_calls, scenario):
    """Score how well the tool arguments capture the expected information.
    Returns 0-1. Checks if expected fields have non-empty, relevant values."""
    if not tool_calls:
        return 0.0
    expected_keys = scenario.get("expected_args", {})
    if not expected_keys:
        return 1.0 if tool_calls else 0.0

    matches = 0
    total = 0
    for tool_name, expected_fields in expected_keys.items():
        matching_calls = [tc for tc in tool_calls if tc["name"] == tool_name]
        if not matching_calls:
            total += len(expected_fields)
            continue
        tc = matching_calls[0]
        for field_name, check_fn in expected_fields.items():
            total += 1
            value = tc["args"].get(field_name, "")
            if callable(check_fn):
                if check_fn(value):
                    matches += 1
            elif isinstance(check_fn, str):
                if check_fn.lower() in str(value).lower():
                    matches += 1
    return matches / total if total > 0 else 1.0


def run_scenario(client, model, scenario, tools, veil, vertical_name):
    """Run a single scenario in both raw and veil modes."""
    user_text = f"{scenario['instruction']}\n\n{scenario['input']}"
    results = []

    # ── RAW MODE ──
    t0 = time.time()
    try:
        resp = call_model(client, model, [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ], tools)
        latency = time.time() - t0
        tool_calls = extract_tool_calls(resp)
        called = [tc["name"] for tc in tool_calls]
        expected = set(scenario["expected_tools"])
        correct = expected & set(called)

        results.append(ScenarioResult(
            scenario=scenario["name"],
            vertical=vertical_name,
            mode="raw",
            accuracy=len(correct) / len(expected) if expected else 1.0,
            tools_called=called,
            tools_expected=list(expected),
            tools_missing=list(expected - set(called)),
            tools_extra=list(set(called) - expected),
            latency=latency,
            pii_detected=0,
            args_quality=score_args_quality(tool_calls, scenario),
        ))
    except Exception as e:
        results.append(ScenarioResult(
            scenario=scenario["name"], vertical=vertical_name, mode="raw", error=str(e),
        ))

    # ── VEIL MODE ──
    t0 = time.time()
    redaction = veil.redact(user_text)
    redact_ms = (time.time() - t0) * 1000

    t0 = time.time()
    try:
        resp = call_model(client, model, [
            {"role": "system", "content": SYSTEM_PROMPT_VEIL},
            {"role": "user", "content": redaction.sanitized},
        ], tools)
        latency = time.time() - t0
        tool_calls = extract_tool_calls(resp)
        called = [tc["name"] for tc in tool_calls]
        expected = set(scenario["expected_tools"])
        correct = expected & set(called)
        leaked = check_pii_leakage(tool_calls, redaction.token_map)

        results.append(ScenarioResult(
            scenario=scenario["name"],
            vertical=vertical_name,
            mode="veil",
            accuracy=len(correct) / len(expected) if expected else 1.0,
            tools_called=called,
            tools_expected=list(expected),
            tools_missing=list(expected - set(called)),
            tools_extra=list(set(called) - expected),
            latency=latency,
            redact_ms=redact_ms,
            pii_detected=redaction.stats.total,
            pii_leaked=len(leaked),
            leaked_details=leaked,
            args_quality=score_args_quality(tool_calls, scenario),
        ))
    except Exception as e:
        results.append(ScenarioResult(
            scenario=scenario["name"], vertical=vertical_name, mode="veil", error=str(e),
        ))

    return results


def print_results(all_results, model):
    raw = [r for r in all_results if r.mode == "raw"]
    veil = [r for r in all_results if r.mode == "veil"]

    avg_acc_raw = sum(r.accuracy for r in raw) / len(raw) if raw else 0
    avg_acc_veil = sum(r.accuracy for r in veil) / len(veil) if veil else 0
    avg_lat_raw = sum(r.latency for r in raw if r.latency) / max(1, len([r for r in raw if r.latency]))
    avg_lat_veil = sum(r.latency for r in veil if r.latency) / max(1, len([r for r in veil if r.latency]))
    avg_redact = sum(r.redact_ms for r in veil) / len(veil) if veil else 0
    total_pii = sum(r.pii_detected for r in veil)
    total_leaked = sum(r.pii_leaked for r in veil)
    avg_args_raw = sum(r.args_quality for r in raw) / len(raw) if raw else 0
    avg_args_veil = sum(r.args_quality for r in veil) / len(veil) if veil else 0
    delta = avg_acc_veil - avg_acc_raw

    print(f"""
{'=' * 70}
VEILPHANTOM BENCHMARK RESULTS — {model}
{'=' * 70}

┌─────────────────────────┬──────────────┬──────────────┐
│ Metric                  │ Without Veil │  With Veil   │
├─────────────────────────┼──────────────┼──────────────┤
│ Tool Accuracy (avg)     │    {avg_acc_raw:>6.0%}      │    {avg_acc_veil:>6.0%}      │
│ Args Quality (avg)      │    {avg_args_raw:>6.0%}      │    {avg_args_veil:>6.0%}      │
│ Avg Model Latency       │    {avg_lat_raw:>5.2f}s      │    {avg_lat_veil:>5.2f}s      │
│ Avg Redaction Time      │       —      │    {avg_redact:>5.1f}ms     │
│ PII Sent to Model       │     ALL      │      0       │
│ PII Detected            │       —      │  {total_pii:>10}  │
│ PII Leaked in Output    │      N/A     │  {total_leaked:>10}  │
│ Accuracy Delta          │              │    {delta:>+5.0%}      │
└─────────────────────────┴──────────────┴──────────────┘
""")

    # Per-vertical breakdown
    verticals_seen = list(dict.fromkeys(r.vertical for r in all_results))
    print(f"{'Vertical':<18} {'Raw Acc':>8} {'Veil Acc':>9} {'Args(R)':>8} {'Args(V)':>8} {'PII Det':>8} {'Leaked':>7}")
    print("─" * 72)
    for vert in verticals_seen:
        v_raw = [r for r in raw if r.vertical == vert]
        v_veil = [r for r in veil if r.vertical == vert]
        r_acc = sum(r.accuracy for r in v_raw) / len(v_raw) if v_raw else 0
        v_acc = sum(r.accuracy for r in v_veil) / len(v_veil) if v_veil else 0
        r_args = sum(r.args_quality for r in v_raw) / len(v_raw) if v_raw else 0
        v_args = sum(r.args_quality for r in v_veil) / len(v_veil) if v_veil else 0
        pii = sum(r.pii_detected for r in v_veil)
        leak = sum(r.pii_leaked for r in v_veil)
        print(f"{vert:<18} {r_acc:>7.0%} {v_acc:>8.0%} {r_args:>7.0%} {v_args:>7.0%} {pii:>8} {leak:>7}")

    # Per-scenario detail
    print(f"\n{'─' * 72}")
    print("Per-scenario detail:")
    print(f"{'Scenario':<35} {'Mode':<6} {'Acc':>5} {'Args':>5} {'PII':>5} {'Leak':>5} {'Lat':>6}")
    print("─" * 72)
    for r in all_results:
        pii_str = str(r.pii_detected) if r.mode == "veil" else "—"
        leak_str = str(r.pii_leaked) if r.mode == "veil" else "—"
        print(f"{r.vertical+'/'+r.scenario:<35} {r.mode:<6} {r.accuracy:>4.0%} {r.args_quality:>4.0%} {pii_str:>5} {leak_str:>5} {r.latency:>5.2f}s")

    if total_leaked == 0:
        print(f"\n✓ ZERO PII LEAKAGE across {len(veil)} scenarios.")
    else:
        print(f"\n⚠ {total_leaked} PII values leaked:")
        for r in veil:
            for d in r.leaked_details:
                print(f"  - {r.vertical}/{r.scenario}: {d}")


def main():
    parser = argparse.ArgumentParser(description="VeilPhantom Benchmark Suite")
    parser.add_argument("--vertical", "-v", type=str, default=None,
                        help="Run only this vertical (e.g. healthcare, financial)")
    parser.add_argument("--model", "-m", type=str, default="anthropic/claude-3.5-haiku",
                        help="Model ID for OpenRouter")
    parser.add_argument("--api-key", type=str, default=None,
                        help="OpenRouter API key (or set OPENROUTER_API_KEY)")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output JSON file path")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: Set OPENROUTER_API_KEY or pass --api-key")
        sys.exit(1)

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    veil = VeilClient(VeilConfig.regex_only())

    verticals_to_run = {args.vertical: VERTICALS[args.vertical]} if args.vertical else VERTICALS

    all_results = []
    total_scenarios = sum(len(v["scenarios"]) for v in verticals_to_run.values())
    print(f"Running {total_scenarios} scenarios across {len(verticals_to_run)} verticals...")
    print(f"Model: {args.model}")

    for vert_name, vert_data in verticals_to_run.items():
        print(f"\n{'═' * 50}")
        print(f"  {vert_name.upper()}")
        print(f"{'═' * 50}")

        for scenario in vert_data["scenarios"]:
            print(f"\n  ► {scenario['name']}", end="", flush=True)
            results = run_scenario(client, args.model, scenario, vert_data["tools"], veil, vert_name)
            all_results.extend(results)

            raw_r = next((r for r in results if r.mode == "raw"), None)
            veil_r = next((r for r in results if r.mode == "veil"), None)
            if raw_r and veil_r:
                print(f"  raw={raw_r.accuracy:.0%} veil={veil_r.accuracy:.0%} pii={veil_r.pii_detected} leak={veil_r.pii_leaked}")
            time.sleep(0.3)

    print_results(all_results, args.model)

    # Save results
    output_path = args.output or str(Path(__file__).parent / "results" / f"benchmark_{int(time.time())}.json")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({
            "model": args.model,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "verticals": list(verticals_to_run.keys()),
            "total_scenarios": total_scenarios,
            "results": [asdict(r) for r in all_results],
        }, f, indent=2, default=str)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
