"""Deduplication against everything already known to the system.

Two things must be true before a contact is treated as new:
  1. Its email isn't already a CRM record (fetched once per discovery run,
     from the *complete*, fully-paginated set - see integrations/crm_client.py
     for why "complete" is load-bearing here).
  2. Its email hasn't already been sent to, or already has a pending draft,
     in local state.

Checking against a single shared snapshot per run (rather than querying the
CRM per-candidate) is what keeps discovery fast and avoids hammering the CRM
API once per lead.
"""
from __future__ import annotations

from src.models import Contact
from src.state.store import StateStore


def dedup_contacts(
    contacts: list[Contact], known_crm_emails: set[str], state: StateStore
) -> list[Contact]:
    seen_in_this_run: set[str] = set()
    result: list[Contact] = []
    for contact in contacts:
        if not contact.email:
            continue
        email = contact.email.lower()
        if email in known_crm_emails:
            continue
        if email in seen_in_this_run:
            continue
        if state.get_contact(email) is not None:
            continue
        seen_in_this_run.add(email)
        result.append(contact)
    return result
