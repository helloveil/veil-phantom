"""
VeilPhantom — Tool-call interception middleware for agentic workflows.

Intercepts LLM tool calls, replaces privacy tokens with real PII values
(locally), executes tools, and re-redacts results before sending back to the LLM.
Real PII never leaves the machine.

Usage::

    from veil_phantom import VeilSession, VeilToolMiddleware

    session = VeilSession()
    result = session.redact(user_input)

    # After LLM returns tool_calls:
    mw = VeilToolMiddleware(session)
    rehydrated = mw.rehydrate_tool_calls(tool_calls)
    # rehydrated[0].rehydrated_args has real values for local execution
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from .session import VeilSession


@dataclass
class RehydratedToolCall:
    """A tool call with both tokenized (private) and rehydrated (real) arguments."""
    id: str
    name: str
    tokenized_args: dict[str, Any]
    rehydrated_args: dict[str, Any]


def _deep_rehydrate(value: Any, session: VeilSession) -> Any:
    """Recursively replace tokens with real values in any JSON-compatible structure."""
    if isinstance(value, str):
        return session.rehydrate(value)
    elif isinstance(value, list):
        return [_deep_rehydrate(item, session) for item in value]
    elif isinstance(value, dict):
        return {k: _deep_rehydrate(v, session) for k, v in value.items()}
    return value


class VeilToolMiddleware:
    """Framework-agnostic tool-call interception middleware."""

    def __init__(self, session: VeilSession, dry_run: bool = False):
        self.session = session
        self.dry_run = dry_run

    def rehydrate_tool_calls(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[RehydratedToolCall]:
        """Rehydrate token-filled tool call arguments with real PII values.

        Args:
            tool_calls: List of tool calls in OpenAI format, each with keys:
                - id: str
                - name: str (function name)
                - args: dict (parsed arguments)

        Returns:
            List of RehydratedToolCall with both tokenized and real args.
        """
        results = []
        for tc in tool_calls:
            tokenized = tc.get("args", {})
            rehydrated = _deep_rehydrate(tokenized, self.session)
            results.append(RehydratedToolCall(
                id=tc.get("id", ""),
                name=tc["name"],
                tokenized_args=tokenized,
                rehydrated_args=rehydrated,
            ))
        return results

    def redact_tool_result(self, result: str) -> str:
        """Re-redact a tool's output before sending back to the LLM.

        Known PII gets existing tokens. New PII gets fresh tokens
        merged into the session.
        """
        return self.session.redact_tool_output(result)

    def process_tool_calls(
        self,
        tool_calls: list[dict[str, Any]],
        tool_registry: dict[str, Callable[..., str]] | None = None,
    ) -> list[dict[str, str]]:
        """Full pipeline: rehydrate args → execute tools → re-redact results.

        Args:
            tool_calls: Raw tool calls from LLM (OpenAI format).
            tool_registry: Map of function_name → callable. If None or dry_run,
                returns rehydrated args as JSON (for inspection/benchmarks).

        Returns:
            List of tool result messages in OpenAI format:
            [{"role": "tool", "tool_call_id": "...", "content": "re-redacted result"}]
        """
        rehydrated = self.rehydrate_tool_calls(tool_calls)
        results = []

        for tc in rehydrated:
            if self.dry_run or tool_registry is None:
                raw_result = json.dumps(tc.rehydrated_args)
            else:
                fn = tool_registry.get(tc.name)
                if fn is None:
                    raw_result = json.dumps({"error": f"Unknown tool: {tc.name}"})
                else:
                    try:
                        raw_result = fn(**tc.rehydrated_args)
                    except Exception as e:
                        raw_result = json.dumps({"error": str(e)})

            safe_result = self.redact_tool_result(str(raw_result))

            results.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": safe_result,
            })

        return results
