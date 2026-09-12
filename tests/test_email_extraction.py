"""Regression test for a real, previously-fixed bug: a phone number glued
directly against an email address with no separator was being swallowed
into the match, producing a garbled local-part.
"""
from src.discovery.contact_extractor import extract_contact_email


def test_mailto_link_is_preferred_over_page_text():
    html = '<a href="mailto:hello@example.com">Email</a><p>info@other.example</p>'
    email, method = extract_contact_email("https://example.com", html)
    assert email == "hello@example.com"
    assert method == "mailto"


def test_regex_fallback_extracts_clean_email_with_separator():
    html = "<p>Call 0400 000 000 or email info@example.com for a quote</p>"
    email, method = extract_contact_email("https://example.com", html)
    assert email == "info@example.com"
    assert method == "regex_fallback"


def test_regex_fallback_recovers_email_glued_to_phone_number():
    # No whitespace between the phone number and the email - this is the
    # exact shape of the original bug.
    html = "<p>Call 0400000005office@example.com for a quote</p>"
    email, method = extract_contact_email("https://example.com", html)
    assert email == "office@example.com"
    assert method == "regex_fallback"


def test_regex_fallback_ignores_emails_on_other_domains():
    html = "<p>Hosted by webbuilder.example - contact hosting@webbuilder.example</p>"
    email, method = extract_contact_email("https://example.com", html)
    assert email is None
    assert method == "none"


def test_no_contact_found_returns_none():
    html = "<p>No contact details here.</p>"
    email, method = extract_contact_email("https://example.com", html)
    assert email is None
    assert method == "none"
