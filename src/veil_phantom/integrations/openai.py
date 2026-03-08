"""
VeilPhantom — OpenAI integration wrapper.

Usage::

    from veil_phantom.integrations.openai import veil_chat
    from openai import OpenAI

    client = OpenAI()
    response = veil_chat(
        client,
        messages=[{"role": "user", "content": "Summarize: John sent $5M to jane@acme.com"}],
    )
    # response.content has original values restored — PII never reached OpenAI
"""

from __future__ import annotations

from typing import Any

from ..client import VeilClient
from ..config import VeilConfig


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
