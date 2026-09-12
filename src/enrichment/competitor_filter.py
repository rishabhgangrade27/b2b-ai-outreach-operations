"""Competitor filtering.

A discovered business whose name matches a known-competitor substring is
dropped before it ever reaches the CRM or drafting stage. This exists
because of a real incident: without this check, the search terms used for
discovery occasionally surfaced the operator's own direct competitors, and
early runs drafted (and in one case sent) outreach to them. The fix is
blunt on purpose - a simple, auditable substring blocklist beats a "smart"
similarity match that a reviewer can't reason about at a glance.
"""
from __future__ import annotations

from src.models import Contact


def is_competitor(contact: Contact, competitor_substrings: tuple[str, ...]) -> bool:
    name = contact.lead.business_name.lower()
    return any(substr.lower() in name for substr in competitor_substrings)


def filter_competitors(contacts: list[Contact], competitor_substrings: tuple[str, ...]) -> list[Contact]:
    return [c for c in contacts if not is_competitor(c, competitor_substrings)]
