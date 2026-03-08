"""
VeilPhantom — LangChain integration.

Usage::

    from veil_phantom.integrations.langchain import VeilRunnable
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI()
    safe_llm = VeilRunnable(llm)

    # PII automatically redacted before reaching LLM, restored after
    response = safe_llm.invoke("Summarize: John sent $5M to jane@acme.com")
"""

from __future__ import annotations

from typing import Any

from ..client import VeilClient
from ..config import VeilConfig


class VeilRunnable:
    """Wraps a LangChain Runnable with VeilPhantom PII protection."""

    def __init__(self, runnable: Any, veil: VeilClient | None = None):
        self.runnable = runnable
        self.veil = veil or VeilClient(VeilConfig.regex_only())

    def invoke(self, input: str | Any, **kwargs: Any) -> str:
        """Invoke the wrapped runnable with PII protection."""
        text = input if isinstance(input, str) else str(input)
        result = self.veil.redact(text)
        response = self.runnable.invoke(result.sanitized, **kwargs)
        content = response.content if hasattr(response, "content") else str(response)
        return result.rehydrate(content)

    async def ainvoke(self, input: str | Any, **kwargs: Any) -> str:
        """Async invoke with PII protection."""
        text = input if isinstance(input, str) else str(input)
        result = self.veil.redact(text)
        response = await self.runnable.ainvoke(result.sanitized, **kwargs)
        content = response.content if hasattr(response, "content") else str(response)
        return result.rehydrate(content)
