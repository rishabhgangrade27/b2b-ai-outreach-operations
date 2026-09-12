"""Outbound email delivery.

Every send goes through here, and every send is gated by DRY_RUN. This is
the single narrowest point in the system where an external, irreversible
side effect can happen - see docs/safety-controls.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class SendResult:
    sent: bool
    dry_run: bool
    to: str
    subject: str


class EmailClient(Protocol):
    def send(self, to: str, subject: str, body: str, dry_run: bool) -> SendResult: ...


class ResendEmailClient:
    """Real implementation - requires EMAIL_PROVIDER_API_KEY. Not used by the demo."""

    def __init__(self, api_key: str, from_address: str, bcc: str | None = None):
        self.api_key = api_key
        self.from_address = from_address
        self.bcc = bcc

    def send(self, to: str, subject: str, body: str, dry_run: bool) -> SendResult:
        if dry_run:
            return SendResult(sent=False, dry_run=True, to=to, subject=subject)

        import resend

        resend.api_key = self.api_key
        resend.Emails.send(
            {
                "from": self.from_address,
                "to": [to],
                "bcc": [self.bcc] if self.bcc else [],
                "subject": subject,
                "text": body,
            }
        )
        return SendResult(sent=True, dry_run=False, to=to, subject=subject)


class MockEmailClient:
    """Records sends in memory instead of calling a real provider."""

    def __init__(self):
        self.outbox: list[SendResult] = []

    def send(self, to: str, subject: str, body: str, dry_run: bool) -> SendResult:
        result = SendResult(sent=not dry_run, dry_run=dry_run, to=to, subject=subject)
        self.outbox.append(result)
        return result
