#!/usr/bin/env python3
"""Local, sanitized walkthrough of the full pipeline:

    discovery -> validation -> enrichment -> CRM -> draft -> approval
    -> safety checks -> rate limiter -> send -> follow-up state

Everything here runs against mock integrations - no network calls, no real
API keys required. It exists to make the workflow *observable*: a reader
should be able to run this and see, stage by stage, what a real run does.

Run it with:
    python demo.py
"""
from __future__ import annotations

import random
from datetime import date

from src.approval.approval_flow import poll_approval, request_approval
from src.config import SETTINGS
from src.discovery.pipeline import run_discovery
from src.enrichment.competitor_filter import filter_competitors
from src.enrichment.dedup import dedup_contacts
from src.enrichment.validators import is_valid_contact
from src.integrations.crm_client import MockCRMClient
from src.integrations.email_client import MockEmailClient
from src.integrations.llm_client import MockLLMClient
from src.integrations.places_client import MockPlacesClient
from src.integrations.slack_client import MockSlackClient
from src.models import ApprovalState
from src.outreach.drafting import draft_initial_outreach
from src.rate_limiter.limiter import can_send_today, daily_cap, days_since, jitter_minutes
from src.state.store import StateStore

SEP = "-" * 70


def step(title: str) -> None:
    print(f"\n{SEP}\n{title}\n{SEP}")


# --- Synthetic fixture: five businesses, one a competitor, one with a
# malformed-HTML contact page to exercise the extraction fallback path. ---
PLACES_FIXTURE = [
    {"name": "Northfield Contracting", "website": "https://northfield.example", "phone": "0400 000 001", "region_key": "region_1", "matched_segments": ["segment a service provider"]},
    {"name": "Our Own Company Pty Ltd", "website": "https://ourowncompany.example", "phone": "0400 000 002", "region_key": "region_1", "matched_segments": ["segment a service provider"]},
    {"name": "Bluepoint Services", "website": "https://bluepoint.example", "phone": "0400 000 003", "region_key": "region_2", "matched_segments": ["segment b service provider"]},
    {"name": "Ridgeline Group", "website": "https://ridgeline.example", "phone": "0400 000 004", "region_key": "region_3", "matched_segments": ["segment c service provider"]},
    {"name": "Harbor Trade Co", "website": "https://harbortrade.example", "phone": "0400 000 005", "region_key": "region_1", "matched_segments": ["segment a service provider"]},
]

WEBSITE_HTML = {
    "https://northfield.example": '<a href="mailto:hello@northfield.example">Email us</a>',
    "https://ourowncompany.example": '<a href="mailto:contact@ourowncompany.example">Contact</a>',
    "https://bluepoint.example": '<p>Call 0400 000 003 or reach us at info@bluepoint.example for quotes.</p>',
    "https://ridgeline.example": '<p>No contact details published here.</p>',
    # Deliberately glued phone+email with no separator, to exercise the
    # word-boundary fallback described in contact_extractor.py.
    "https://harbortrade.example": '<p>Call 0400000005office@harbortrade.example for a quote</p>',
}


def main() -> None:
    rng = random.Random(7)  # fixed seed so demo output is reproducible
    state = StateStore(path="demo_state.json")
    crm = MockCRMClient()
    slack = MockSlackClient()
    email_client = MockEmailClient()
    llm_client = MockLLMClient()

    step("1. LEAD DISCOVERY (region x segment search)")
    contacts = run_discovery(SETTINGS, MockPlacesClient(PLACES_FIXTURE), WEBSITE_HTML)
    for c in contacts:
        print(f"  found: {c.lead.business_name:<28} email={c.email!r:<45} via={c.extraction_method}")

    step("2. VALIDATION (drop unusable/malformed contacts)")
    valid_contacts = [c for c in contacts if is_valid_contact(c)]
    dropped = len(contacts) - len(valid_contacts)
    print(f"  {len(valid_contacts)} valid, {dropped} dropped (no usable email)")

    step("3. ENRICHMENT (competitor filter + dedup)")
    filtered = filter_competitors(valid_contacts, SETTINGS.competitor_name_substrings)
    print(f"  competitor filter removed {len(valid_contacts) - len(filtered)}: "
          f"{[c.lead.business_name for c in valid_contacts if c not in filtered]}")
    known_crm_emails = {item["email"] for item in crm.get_all_items(board_id="demo-board")}
    deduped = dedup_contacts(filtered, known_crm_emails, state)
    print(f"  {len(deduped)} new contacts after dedup against CRM + local state")

    step("4. CRM RECORD CREATION")
    for c in deduped:
        item_id = crm.create_item("demo-board", {"email": c.email, "name": c.lead.business_name, "stage": "new"})
        print(f"  created CRM item {item_id} for {c.lead.business_name} ({c.email})")

    step("5. AI-ASSISTED OUTREACH DRAFTING")
    drafts = [draft_initial_outreach(c, llm_client) for c in deduped]
    for d in drafts:
        print(f"  draft for {d.contact_email} [{d.generated_by} / {d.template_key}]: \"{d.subject}\"")

    step("6. HUMAN APPROVAL (Slack reaction simulation)")
    approval_channel = "#outreach-approvals"
    requests = [request_approval(d, slack, approval_channel) for d in drafts]
    # Simulate a human: approve all but the last one, to show a rejection
    # halting that contact's cadence permanently.
    for i, req in enumerate(requests):
        reaction = "rejected" if i == len(requests) - 1 else "approved"
        slack.simulate_reaction(req.message_id, reaction)  # type: ignore[attr-defined]
        req = poll_approval(req, slack, approval_channel, state)
        print(f"  {req.draft.contact_email}: {req.state.value}"
              + ("  -> halted, will never re-enter cadence" if req.state == ApprovalState.REJECTED else ""))

    approved = [r for r in requests if r.state == ApprovalState.APPROVED]

    step("7. SAFETY CHECKS + RATE LIMITER")
    start_date = date(2026, 1, 1)
    today = date(2026, 1, 3)
    days_elapsed = days_since(start_date, today)
    cap = daily_cap(days_elapsed, SETTINGS.warmup_tiers, rng)
    print(f"  day {days_elapsed} of operation -> warmup tier cap for today: {cap} sends")

    step("8. CONTROLLED SEND")
    sent_count = 0
    for req in approved:
        if not can_send_today(sent_count, days_elapsed, SETTINGS.warmup_tiers, rng):
            print(f"  {req.draft.contact_email}: SKIPPED - daily cap reached, will retry tomorrow")
            continue
        wait = jitter_minutes(SETTINGS.pre_send_jitter_minutes, rng)
        result = email_client.send(req.draft.contact_email, req.draft.subject, req.draft.body, dry_run=SETTINGS.dry_run)
        state.record_sent(req.draft.contact_email, "initial", today.isoformat())
        sent_count += 1
        mode = "DRY RUN (no real email sent)" if result.dry_run else "SENT"
        print(f"  {req.draft.contact_email}: queued with {wait}min jitter -> {mode}")

    step("9. FOLLOW-UP STATE")
    for req in approved:
        stages = state.sent_stages(req.draft.contact_email)
        halted = state.is_halted(req.draft.contact_email)
        print(f"  {req.draft.contact_email}: sent_stages={stages} halted={halted} "
              f"-> next eligible follow-up in {SETTINGS.followup_day_offsets[0]} days (if not halted)")

    print(f"\n{SEP}\nDemo complete. State written to demo_state.json (safe to delete).\n{SEP}")


if __name__ == "__main__":
    main()
