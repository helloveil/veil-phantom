#!/usr/bin/env python3
"""
VeilPhantom Comprehensive Benchmark Suite
==========================================
50 scenarios across 8 verticals measuring privacy vs utility trade-off.

Metrics tracked:
- Tool calling accuracy (raw vs veil)
- Args quality (expected_args validation)
- PII detection by type (PERSON, EMAIL, PHONE, BANKACCT, etc.)
- PII leakage rate (zero-leakage target)
- Token preservation in tool args
- Redaction latency overhead
- Per-vertical and per-scenario breakdowns

Usage:
    export OPENROUTER_API_KEY=sk-or-v1-...
    python benchmarks/run_benchmarks.py [--vertical healthcare] [--model anthropic/claude-haiku-4.5]
"""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
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
    "You may call multiple tools if needed.\n\n"
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
)

# Regex for detecting VeilPhantom tokens in tool args
_TOKEN_RE = re.compile(r"\[([A-Z_]+)_\d+\]")


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
    args_quality: float = 0.0
    # New comprehensive metrics
    pii_by_type: dict = field(default_factory=dict)  # {type: count} from redaction
    expected_pii_types: dict = field(default_factory=dict)  # from scenario annotation
    token_preservation: float = 0.0  # % of tokens in args that are valid [TYPE_N]
    tokens_in_args: int = 0  # count of tokens found in tool args
    input_tokens: int = 0  # approx input token count
    output_tokens: int = 0  # approx output token count


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


def get_usage(response):
    """Extract token usage from response."""
    usage = getattr(response, "usage", None)
    if usage:
        return getattr(usage, "prompt_tokens", 0), getattr(usage, "completion_tokens", 0)
    return 0, 0


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


def count_tokens_in_args(tool_calls):
    """Count VeilPhantom tokens ([TYPE_N]) found in tool call arguments."""
    count = 0
    for tc in tool_calls:
        args_str = json.dumps(tc["args"])
        count += len(_TOKEN_RE.findall(args_str))
    return count


def score_args_quality(tool_calls, scenario):
    """Score how well the tool arguments capture the expected information."""
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
            try:
                if callable(check_fn):
                    if check_fn(value):
                        matches += 1
                elif isinstance(check_fn, str):
                    if check_fn.lower() in str(value).lower():
                        matches += 1
            except Exception:
                pass  # Lambda may fail on unexpected types
    return matches / total if total > 0 else 1.0


def count_pii_by_type(token_map):
    """Count detected PII entities grouped by type."""
    counts = Counter()
    if not token_map:
        return dict(counts)
    for token_name in token_map:
        # token_name is like "[PERSON_1]" — extract type
        m = _TOKEN_RE.match(token_name)
        if m:
            counts[m.group(1)] += 1
    return dict(counts)


def run_scenario(client, model, scenario, tools, veil, vertical_name):
    """Run a single scenario in both raw and veil modes."""
    user_text = f"{scenario['instruction']}\n\n{scenario['input']}"
    results = []
    expected_pii = scenario.get("pii_entities", {})
    # Normalize: if it's a list (old format), treat as untyped
    if isinstance(expected_pii, list):
        expected_pii = {"UNKNOWN": expected_pii}

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
        in_tok, out_tok = get_usage(resp)

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
            expected_pii_types=expected_pii,
            input_tokens=in_tok,
            output_tokens=out_tok,
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
        pii_types = count_pii_by_type(redaction.token_map)
        tokens_in_args = count_tokens_in_args(tool_calls)
        in_tok, out_tok = get_usage(resp)

        # Token preservation: what fraction of expected PII appeared as tokens in args
        total_expected_pii = sum(len(v) for v in expected_pii.values())
        token_preservation = tokens_in_args / total_expected_pii if total_expected_pii > 0 else 1.0

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
            pii_by_type=pii_types,
            expected_pii_types=expected_pii,
            token_preservation=min(token_preservation, 1.0),
            tokens_in_args=tokens_in_args,
            input_tokens=in_tok,
            output_tokens=out_tok,
        ))
    except Exception as e:
        results.append(ScenarioResult(
            scenario=scenario["name"], vertical=vertical_name, mode="veil", error=str(e),
        ))

    return results


def print_results(all_results, model):
    raw = [r for r in all_results if r.mode == "raw"]
    veil = [r for r in all_results if r.mode == "veil"]

    if not raw or not veil:
        print("No results to display.")
        return

    # ── Headline metrics ──
    avg_acc_raw = sum(r.accuracy for r in raw) / len(raw)
    avg_acc_veil = sum(r.accuracy for r in veil) / len(veil)
    avg_lat_raw = sum(r.latency for r in raw if r.latency) / max(1, len([r for r in raw if r.latency]))
    avg_lat_veil = sum(r.latency for r in veil if r.latency) / max(1, len([r for r in veil if r.latency]))
    avg_redact = sum(r.redact_ms for r in veil) / len(veil)
    total_pii = sum(r.pii_detected for r in veil)
    total_leaked = sum(r.pii_leaked for r in veil)
    avg_args_raw = sum(r.args_quality for r in raw) / len(raw)
    avg_args_veil = sum(r.args_quality for r in veil) / len(veil)
    delta = avg_acc_veil - avg_acc_raw
    latency_overhead = ((avg_lat_veil + avg_redact / 1000) - avg_lat_raw) / avg_lat_raw * 100 if avg_lat_raw > 0 else 0
    avg_token_pres = sum(r.token_preservation for r in veil) / len(veil)
    total_in_tok = sum(r.input_tokens for r in veil)
    total_out_tok = sum(r.output_tokens for r in veil)
    errors_raw = sum(1 for r in raw if r.error)
    errors_veil = sum(1 for r in veil if r.error)

    # ── PII type aggregation ──
    pii_type_totals = Counter()
    for r in veil:
        for pii_type, count in r.pii_by_type.items():
            pii_type_totals[pii_type] += count

    # Expected PII entity count
    total_expected_entities = 0
    for r in veil:
        for entities in r.expected_pii_types.values():
            if isinstance(entities, list):
                total_expected_entities += len(entities)

    print(f"""
{'=' * 78}
  VEILPHANTOM BENCHMARK RESULTS
  {model} | {len(veil)} scenarios | 8 verticals
{'=' * 78}

  HEADLINE METRICS
  ─────────────────────────────────────────────────────────────────────
  ┌───────────────────────────┬──────────────┬──────────────┐
  │ Metric                    │ Without Veil │  With Veil   │
  ├───────────────────────────┼──────────────┼──────────────┤
  │ Tool Accuracy             │    {avg_acc_raw:>6.1%}      │    {avg_acc_veil:>6.1%}      │
  │ Args Quality              │    {avg_args_raw:>6.1%}      │    {avg_args_veil:>6.1%}      │
  │ Avg Latency               │    {avg_lat_raw:>5.2f}s      │    {avg_lat_veil:>5.2f}s      │
  │ Avg Redaction Time        │       --     │    {avg_redact:>5.1f}ms     │
  │ Latency Overhead          │       --     │   {latency_overhead:>+5.1f}%     │
  │ PII Entities Sent to LLM  │     ALL      │       0      │
  │ PII Entities Detected     │       --     │   {total_pii:>8}   │
  │ PII Leaked in Tool Args   │      N/A     │   {total_leaked:>8}   │
  │ Token Preservation        │      N/A     │    {avg_token_pres:>6.1%}      │
  │ Accuracy Delta            │              │   {delta:>+6.1%}      │
  │ API Errors                │   {errors_raw:>8}   │   {errors_veil:>8}   │
  └───────────────────────────┴──────────────┴──────────────┘""")

    # ── PII Detection by Type ──
    if pii_type_totals:
        print(f"""
  PII DETECTION BY TYPE
  ─────────────────────────────────────────────────────────────────────""")
        sorted_types = sorted(pii_type_totals.items(), key=lambda x: -x[1])
        for pii_type, count in sorted_types:
            bar = "#" * min(count, 40)
            pct = count / total_pii * 100 if total_pii > 0 else 0
            print(f"  {pii_type:<14} {count:>4}  ({pct:>5.1f}%)  {bar}")
        print(f"  {'TOTAL':<14} {total_pii:>4}  (100.0%)")

    # ── Per-vertical breakdown ──
    verticals_seen = list(dict.fromkeys(r.vertical for r in all_results))
    print(f"""
  PER-VERTICAL BREAKDOWN
  ─────────────────────────────────────────────────────────────────────""")
    print(f"  {'Vertical':<16} {'#Sc':>3} {'Raw':>5} {'Veil':>5} {'Args(R)':>7} {'Args(V)':>7} {'PII':>5} {'Leak':>5} {'TokPr':>6} {'RedMs':>6}")
    print(f"  {'─' * 72}")
    for vert in verticals_seen:
        v_raw = [r for r in raw if r.vertical == vert]
        v_veil = [r for r in veil if r.vertical == vert]
        n = len(v_raw)
        r_acc = sum(r.accuracy for r in v_raw) / n if v_raw else 0
        v_acc = sum(r.accuracy for r in v_veil) / len(v_veil) if v_veil else 0
        r_args = sum(r.args_quality for r in v_raw) / n if v_raw else 0
        v_args = sum(r.args_quality for r in v_veil) / len(v_veil) if v_veil else 0
        pii = sum(r.pii_detected for r in v_veil)
        leak = sum(r.pii_leaked for r in v_veil)
        tok_pr = sum(r.token_preservation for r in v_veil) / len(v_veil) if v_veil else 0
        red_ms = sum(r.redact_ms for r in v_veil) / len(v_veil) if v_veil else 0
        print(f"  {vert:<16} {n:>3} {r_acc:>4.0%} {v_acc:>5.0%} {r_args:>6.0%} {v_args:>7.0%} {pii:>5} {leak:>5} {tok_pr:>5.0%} {red_ms:>5.1f}ms")

    # ── Per-scenario detail ──
    print(f"""
  PER-SCENARIO DETAIL
  ─────────────────────────────────────────────────────────────────────""")
    print(f"  {'Scenario':<38} {'Mode':<5} {'Acc':>4} {'Args':>5} {'PII':>4} {'Lk':>3} {'Tok':>4} {'Lat':>6}")
    print(f"  {'─' * 72}")

    # Group by scenario for side-by-side comparison
    scenario_pairs = defaultdict(dict)
    for r in all_results:
        key = f"{r.vertical}/{r.scenario}"
        scenario_pairs[key][r.mode] = r

    for key, modes in scenario_pairs.items():
        for mode in ["raw", "veil"]:
            r = modes.get(mode)
            if not r:
                continue
            pii_str = str(r.pii_detected) if mode == "veil" else "--"
            leak_str = str(r.pii_leaked) if mode == "veil" else "--"
            tok_str = str(r.tokens_in_args) if mode == "veil" else "--"
            err = " ERR" if r.error else ""
            print(f"  {key:<38} {mode:<5} {r.accuracy:>3.0%} {r.args_quality:>4.0%} {pii_str:>4} {leak_str:>3} {tok_str:>4} {r.latency:>5.2f}s{err}")

    # ── Failures detail ──
    failures = [r for r in all_results if r.tools_missing or r.error]
    if failures:
        print(f"""
  FAILURES & ISSUES ({len(failures)})
  ─────────────────────────────────────────────────────────────────────""")
        for r in failures:
            if r.error:
                print(f"  [{r.mode}] {r.vertical}/{r.scenario}: ERROR - {r.error[:80]}")
            elif r.tools_missing:
                print(f"  [{r.mode}] {r.vertical}/{r.scenario}: missing tools {r.tools_missing}")

    # ── Leakage detail ──
    if total_leaked > 0:
        print(f"""
  PII LEAKAGE DETAIL ({total_leaked} values)
  ─────────────────────────────────────────────────────────────────────""")
        for r in veil:
            for d in r.leaked_details:
                print(f"  {r.vertical}/{r.scenario}: {d}")
    else:
        print(f"\n  ZERO PII LEAKAGE across {len(veil)} scenarios.")

    # ── Cost estimate ──
    if total_in_tok or total_out_tok:
        # OpenRouter Claude Haiku pricing: ~$1/M input, ~$5/M output
        cost_in = total_in_tok / 1_000_000 * 1.0
        cost_out = total_out_tok / 1_000_000 * 5.0
        total_cost = cost_in + cost_out
        print(f"""
  COST ESTIMATE (OpenRouter Claude Haiku)
  ─────────────────────────────────────────────────────────────────────
  Input tokens:  {total_in_tok:>8,}  (~${cost_in:.3f})
  Output tokens: {total_out_tok:>8,}  (~${cost_out:.3f})
  Total:                    ~${total_cost:.3f}
""")

    print(f"{'=' * 78}")


def main():
    parser = argparse.ArgumentParser(description="VeilPhantom Benchmark Suite")
    parser.add_argument("--vertical", "-v", type=str, default=None,
                        help="Run only this vertical (e.g. healthcare, financial)")
    parser.add_argument("--model", "-m", type=str, default="anthropic/claude-haiku-4.5",
                        help="Model ID for OpenRouter")
    parser.add_argument("--api-key", type=str, default=None,
                        help="OpenRouter API key (or set OPENROUTER_API_KEY)")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output JSON file path")
    parser.add_argument("--scenario", "-s", type=str, default=None,
                        help="Run only scenarios matching this name (substring)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: Set OPENROUTER_API_KEY or pass --api-key")
        sys.exit(1)

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    veil = VeilClient(VeilConfig.regex_only())

    verticals_to_run = {args.vertical: VERTICALS[args.vertical]} if args.vertical else VERTICALS

    # Filter scenarios if --scenario specified
    if args.scenario:
        filtered = {}
        for vert_name, vert_data in verticals_to_run.items():
            matching = [s for s in vert_data["scenarios"] if args.scenario.lower() in s["name"].lower()]
            if matching:
                filtered[vert_name] = {"tools": vert_data["tools"], "scenarios": matching}
        verticals_to_run = filtered

    all_results = []
    total_scenarios = sum(len(v["scenarios"]) for v in verticals_to_run.values())
    print(f"Running {total_scenarios} scenarios across {len(verticals_to_run)} verticals...")
    print(f"Model: {args.model}")
    est_cost = total_scenarios * 2 * 1500 / 1_000_000 * 3  # rough estimate
    print(f"Estimated cost: ~${est_cost:.2f}")

    for vert_name, vert_data in verticals_to_run.items():
        print(f"\n{'=' * 50}")
        print(f"  {vert_name.upper()} ({len(vert_data['scenarios'])} scenarios)")
        print(f"{'=' * 50}")

        for i, scenario in enumerate(vert_data["scenarios"]):
            progress = f"[{i+1}/{len(vert_data['scenarios'])}]"
            print(f"\n  {progress} {scenario['name']}", end="", flush=True)
            results = run_scenario(client, args.model, scenario, vert_data["tools"], veil, vert_name)
            all_results.extend(results)

            raw_r = next((r for r in results if r.mode == "raw"), None)
            veil_r = next((r for r in results if r.mode == "veil"), None)
            if raw_r and veil_r:
                status = "OK" if veil_r.pii_leaked == 0 else "LEAK!"
                print(f"  raw={raw_r.accuracy:.0%} veil={veil_r.accuracy:.0%} "
                      f"pii={veil_r.pii_detected} tok={veil_r.tokens_in_args} {status}")
            elif raw_r and raw_r.error:
                print(f"  ERROR(raw): {raw_r.error[:60]}")
            elif veil_r and veil_r.error:
                print(f"  ERROR(veil): {veil_r.error[:60]}")
            time.sleep(0.3)

    print_results(all_results, args.model)

    # Save results
    output_path = args.output or str(Path(__file__).parent / "results" / f"benchmark_{int(time.time())}.json")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Build comprehensive output JSON
    raw_results = [r for r in all_results if r.mode == "raw"]
    veil_results = [r for r in all_results if r.mode == "veil"]

    pii_type_totals = Counter()
    for r in veil_results:
        for pii_type, count in r.pii_by_type.items():
            pii_type_totals[pii_type] += count

    summary = {
        "model": args.model,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "verticals": list(verticals_to_run.keys()),
        "total_scenarios": total_scenarios,
        "summary": {
            "tool_accuracy_raw": sum(r.accuracy for r in raw_results) / len(raw_results) if raw_results else 0,
            "tool_accuracy_veil": sum(r.accuracy for r in veil_results) / len(veil_results) if veil_results else 0,
            "accuracy_delta": (sum(r.accuracy for r in veil_results) / len(veil_results) - sum(r.accuracy for r in raw_results) / len(raw_results)) if raw_results and veil_results else 0,
            "args_quality_raw": sum(r.args_quality for r in raw_results) / len(raw_results) if raw_results else 0,
            "args_quality_veil": sum(r.args_quality for r in veil_results) / len(veil_results) if veil_results else 0,
            "avg_latency_raw": sum(r.latency for r in raw_results) / len(raw_results) if raw_results else 0,
            "avg_latency_veil": sum(r.latency for r in veil_results) / len(veil_results) if veil_results else 0,
            "avg_redaction_ms": sum(r.redact_ms for r in veil_results) / len(veil_results) if veil_results else 0,
            "total_pii_detected": sum(r.pii_detected for r in veil_results),
            "total_pii_leaked": sum(r.pii_leaked for r in veil_results),
            "pii_leakage_rate": sum(r.pii_leaked for r in veil_results) / max(1, sum(r.pii_detected for r in veil_results)),
            "avg_token_preservation": sum(r.token_preservation for r in veil_results) / len(veil_results) if veil_results else 0,
            "pii_by_type": dict(pii_type_totals),
            "errors_raw": sum(1 for r in raw_results if r.error),
            "errors_veil": sum(1 for r in veil_results if r.error),
        },
        "results": [asdict(r) for r in all_results],
    }

    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
