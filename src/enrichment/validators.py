"""Contact validation - a scraped candidate only becomes an actionable
outreach target once it passes basic sanity checks. Extraction can produce
noise (footer badges, malformed matches); validation is what keeps that
noise out of the CRM and out of drafting.
"""
from __future__ import annotations

import re

from src.models import Contact

_VALID_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,10}$")

_REJECTED_LOCAL_PARTS = {"noreply", "no-reply", "donotreply", "webmaster", "postmaster"}


def is_valid_contact(contact: Contact) -> bool:
    if not contact.email:
        return False
    if not _VALID_EMAIL_RE.match(contact.email):
        return False
    local_part = contact.email.split("@", 1)[0].lower()
    if local_part in _REJECTED_LOCAL_PARTS:
        return False
    return True
