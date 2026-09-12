"""LLM client interface for AI-assisted drafting.

The real integration point is an Anthropic Messages API call. This module
defines the interface plus a mock so the rest of the codebase (and the demo)
never has to know or care whether it's talking to a live model.
"""
from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


class AnthropicLLMClient:
    """Real implementation - requires ANTHROPIC_API_KEY. Not used by the demo."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=600,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text


class MockLLMClient:
    """Deterministic stand-in used by tests and the local demo."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return (
            "Hi there,\n\n"
            "Saw your business come up in our research on companies in your space. "
            "Wanted to reach out directly rather than through a generic list - happy "
            "to share more if it's relevant.\n\n"
            "Worth a quick chat?\n\n"
            "Best,\nOutreach Team"
        )
