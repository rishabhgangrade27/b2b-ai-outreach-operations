"""Human-in-the-loop approval.

This is the architectural centerpiece: nothing drafted by the pipeline can
reach the rate limiter or the email client without a human explicitly
approving it first. Approval is a Slack message + reaction, not a bespoke
UI - a checkmark approves, a cross rejects and halts the contact
permanently (see cadence/followup_scheduler.py for what "halted" means
downstream).
"""
from __future__ import annotations

from src.integrations.slack_client import SlackClient
from src.models import ApprovalRequest, ApprovalState, Draft
from src.state.store import StateStore


def request_approval(draft: Draft, slack_client: SlackClient, channel: str) -> ApprovalRequest:
    text = f"Approve outreach to {draft.contact_email}?\n\nSubject: {draft.subject}\n\n{draft.body}\n\n(react check to approve, x to reject)"
    message_id = slack_client.post_message(channel, text)
    request = ApprovalRequest(draft=draft)
    request.message_id = message_id  # type: ignore[attr-defined]
    return request


def poll_approval(
    request: ApprovalRequest, slack_client: SlackClient, channel: str, state: StateStore
) -> ApprovalRequest:
    reaction = slack_client.get_reaction(channel, request.message_id)  # type: ignore[attr-defined]
    if reaction == "approved":
        request.state = ApprovalState.APPROVED
    elif reaction == "rejected":
        request.state = ApprovalState.REJECTED
        state.halt(request.draft.contact_email)
    return request
