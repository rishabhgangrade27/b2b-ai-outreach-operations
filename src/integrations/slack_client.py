"""Slack integration - approval requests, operator commands, notifications.

Approval is modeled as: post a message, wait for a reaction. A checkmark
reaction approves; a cross rejects and halts the contact's cadence. This
keeps the human-in-the-loop step outside the codebase entirely - approval
lives in a tool people already have open all day, not a bespoke UI.
"""
from __future__ import annotations

from typing import Protocol


class SlackClient(Protocol):
    def post_message(self, channel: str, text: str) -> str: ...
    def get_reaction(self, channel: str, message_id: str) -> str | None: ...


class RealSlackClient:
    """Real implementation - requires SLACK_BOT_TOKEN. Not used by the demo."""

    def __init__(self, bot_token: str):
        from slack_sdk import WebClient

        self.client = WebClient(token=bot_token)

    def post_message(self, channel: str, text: str) -> str:
        resp = self.client.chat_postMessage(channel=channel, text=text)
        return resp["ts"]

    def get_reaction(self, channel: str, message_id: str) -> str | None:
        resp = self.client.reactions_get(channel=channel, timestamp=message_id)
        reactions = resp.get("message", {}).get("reactions", [])
        if any(r["name"] in ("white_check_mark", "heavy_check_mark") for r in reactions):
            return "approved"
        if any(r["name"] in ("x", "no_entry_sign") for r in reactions):
            return "rejected"
        return None


class MockSlackClient:
    """In-memory Slack stand-in for tests and the demo.

    Call `simulate_reaction(message_id, "approved" | "rejected")` to drive
    the approval flow without a real Slack workspace.
    """

    def __init__(self):
        self._messages: dict[str, str] = {}
        self._reactions: dict[str, str] = {}
        self._counter = 0

    def post_message(self, channel: str, text: str) -> str:
        self._counter += 1
        message_id = f"mock-msg-{self._counter}"
        self._messages[message_id] = text
        return message_id

    def get_reaction(self, channel: str, message_id: str) -> str | None:
        return self._reactions.get(message_id)

    def simulate_reaction(self, message_id: str, reaction: str) -> None:
        assert reaction in ("approved", "rejected")
        self._reactions[message_id] = reaction
