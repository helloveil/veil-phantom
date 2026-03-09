"""
VeilPhantom — OpenAI integration wrappers.

Usage::

    from veil_phantom.integrations.openai import veil_chat, veil_agent
    from openai import OpenAI

    # Simple chat (no tools):
    response = veil_chat(client, messages=[...])

    # Agentic with tools (PII never leaves your machine):
    response, session = veil_agent(
        client, messages=[...], tools=[...],
        tool_registry={"send_email": my_send_email_fn},
    )
"""

from __future__ import annotations

import json
from typing import Any, Callable

from ..client import VeilClient
from ..config import VeilConfig
from ..middleware import VeilToolMiddleware
from ..session import VeilSession


def veil_chat(
    client: Any,
    messages: list[dict[str, str]],
    veil: VeilClient | None = None,
    **kwargs: Any,
) -> Any:
    """Wrap an OpenAI chat completion with VeilPhantom PII protection.

    Redacts PII from the last user message, sends sanitized text to OpenAI,
    then rehydrates the response with original values.

    Args:
        client: OpenAI client instance.
        messages: Chat messages (OpenAI format).
        veil: VeilClient instance (creates one if not provided).
        **kwargs: Additional arguments passed to client.chat.completions.create().

    Returns:
        OpenAI ChatCompletion with rehydrated content.
    """
    if veil is None:
        veil = VeilClient(VeilConfig.regex_only())

    # Find last user message and redact it
    result = None
    safe_messages = list(messages)
    for i in range(len(safe_messages) - 1, -1, -1):
        if safe_messages[i].get("role") == "user":
            result = veil.redact(safe_messages[i]["content"])
            safe_messages[i] = {**safe_messages[i], "content": result.sanitized}
            break

    # Call OpenAI
    response = client.chat.completions.create(messages=safe_messages, **kwargs)

    # Rehydrate if we redacted
    if result and response.choices:
        original_content = response.choices[0].message.content
        if original_content:
            response.choices[0].message.content = result.rehydrate(original_content)

    return response


# ── Veil system prompt injected into agentic conversations ──

_VEIL_AGENT_SYSTEM_SUFFIX = (
    "\n\nIMPORTANT: The user's message contains privacy tokens in the format [TYPE_N] "
    "(e.g. [PERSON_1], [EMAIL_1], [AMOUNT_1], [BANKACCT_1], [ORG_1], [PHONE_1], [DATE_1]). "
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


def veil_agent(
    client: Any,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    tool_registry: dict[str, Callable[..., str]] | None = None,
    veil: VeilClient | None = None,
    session: VeilSession | None = None,
    system_prompt: str | None = None,
    max_turns: int = 10,
    dry_run: bool = False,
    **kwargs: Any,
) -> tuple[Any, VeilSession]:
    """Run an agentic tool-calling loop with full VeilPhantom PII protection.

    Data flow:
        1. Redacts user messages (PII → tokens)
        2. Sends sanitized text + tools to LLM
        3. If LLM returns tool_calls:
           a. Rehydrates tool args (tokens → real values, locally)
           b. Executes tools with real values (PII never leaves machine)
           c. Re-redacts tool results (real values → tokens)
           d. Sends re-redacted results back to LLM
           e. Repeats until LLM returns text or max_turns reached
        4. Rehydrates final text response (tokens → real values)

    Args:
        client: OpenAI-compatible client.
        messages: Chat messages (OpenAI format).
        tools: Tool definitions (OpenAI function calling format).
        tool_registry: Map of function_name → callable for local execution.
            If None, dry_run mode is used automatically.
        veil: VeilClient instance (uses session's client if not provided).
        session: Existing VeilSession to reuse (for multi-turn conversations).
        system_prompt: Base system prompt. Veil instructions are appended automatically.
        max_turns: Safety limit on tool-calling loop iterations.
        dry_run: If True, skip tool execution and return rehydrated args as results.
        **kwargs: Additional arguments passed to client.chat.completions.create().

    Returns:
        Tuple of (final ChatCompletion with rehydrated content, VeilSession).
        Keep the session to continue the conversation with accumulated PII context.
    """
    if session is None:
        session = VeilSession(veil=veil)

    middleware = VeilToolMiddleware(session, dry_run=dry_run)

    # Build conversation with redacted user messages
    conv = []
    for msg in messages:
        if msg.get("role") == "system":
            # Append veil instructions to system prompt
            conv.append({**msg, "content": msg["content"] + _VEIL_AGENT_SYSTEM_SUFFIX})
        elif msg.get("role") == "user":
            result = session.redact(msg["content"])
            conv.append({**msg, "content": result.sanitized})
        else:
            conv.append(msg)

    # Ensure there's a system prompt with veil instructions
    if not any(m.get("role") == "system" for m in conv):
        base = system_prompt or "You are a helpful assistant with access to tools."
        conv.insert(0, {"role": "system", "content": base + _VEIL_AGENT_SYSTEM_SUFFIX})

    # Agent loop
    for _ in range(max_turns):
        response = client.chat.completions.create(
            messages=conv, tools=tools, **kwargs
        )

        msg = response.choices[0].message

        # If no tool calls, we're done
        if not msg.tool_calls:
            # Rehydrate final text response
            if msg.content:
                response.choices[0].message.content = session.rehydrate(msg.content)
            return response, session

        # Append assistant message with tool calls to conversation
        conv.append({
            "role": "assistant",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        })

        # Parse, rehydrate, execute, re-redact
        parsed_calls = []
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                args = {}
            parsed_calls.append({
                "id": tc.id,
                "name": tc.function.name,
                "args": args,
            })

        tool_results = middleware.process_tool_calls(parsed_calls, tool_registry)
        conv.extend(tool_results)

    # Max turns reached — return last response
    if msg.content:
        response.choices[0].message.content = session.rehydrate(msg.content)
    return response, session
