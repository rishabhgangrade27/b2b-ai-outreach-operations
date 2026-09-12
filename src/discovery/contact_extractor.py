"""Extracts a contact email from a business's own website.

Two-tier strategy, in priority order:
  1. Look for a `mailto:` link - highest confidence, it's what the business
     itself published as its contact address.
  2. Fall back to a regex scan of visible text, restricted to the site's own
     registrable domain (never harvest an email that belongs to a different
     domain than the one being scraped - that's almost always a footer badge,
     a hosting provider, or a third-party widget, not the business itself).

The regex fallback exists because of a real, previously-fixed bug: an early
version scanned raw page text with a naive email pattern and occasionally
matched a phone number that was glued directly against an email with no
separator in the DOM (e.g. "0400000005office@example.com" rendered with no
whitespace between the phone number and the address), producing a garbled
local-part like "0400000005office". The fix is the constraint below: a
valid local-part must *start* with a letter. That's not a general email-
spec rule, but it's true of every real address this system has ever seen,
and it means the regex simply never starts a match inside a run of digits
- it starts at the first letter, so "office@example.com" is recovered
cleanly instead of the digits being swallowed into the match.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

_MAILTO_RE = re.compile(r'mailto:([^"\'?&\s]+)', re.IGNORECASE)
_EMAIL_RE = re.compile(r"[A-Za-z][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,10}\b")


def _registrable_domain(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def extract_contact_email(website_url: str, html: str) -> tuple[str | None, str]:
    """Returns (email, extraction_method)."""
    mailto_match = _MAILTO_RE.search(html)
    if mailto_match:
        return mailto_match.group(1).strip(), "mailto"

    site_domain = _registrable_domain(website_url)
    for candidate in _EMAIL_RE.findall(html):
        candidate_domain = candidate.split("@", 1)[1].lower()
        if candidate_domain == site_domain or candidate_domain.endswith(f".{site_domain}"):
            return candidate, "regex_fallback"

    return None, "none"
