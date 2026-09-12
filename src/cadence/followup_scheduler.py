"""Follow-up cadence: Day 4 and Week 2, each requiring its own approval.

Two rules that matter more than the exact day offsets:

  1. A halted contact (rejected once, or explicitly halted via an operator
     command) never re-enters cadence, at any stage - halt is permanent,
     not "skip this one send."
  2. A later stage cannot fire while an earlier stage's draft is still
     awaiting approval - otherwise a slow-to-approve Day 4 draft and an
     already-due Week 2 draft could both land in the same approval queue,
     confusing the approver about which one is current.
"""
from __future__ import annotations

from datetime import date

from src.state.store import StateStore

_STAGE_LABELS = {4: "followup_day4", 14: "followup_week2"}


def due_followup_stage(
    first_sent_date: date, today: date, contact_email: str, state: StateStore, offsets: tuple[int, ...]
) -> str | None:
    if state.is_halted(contact_email):
        return None

    already_sent = set(state.sent_stages(contact_email))
    days_elapsed = (today - first_sent_date).days

    for offset in sorted(offsets):
        label = _STAGE_LABELS.get(offset, f"followup_day{offset}")
        if label in already_sent:
            continue
        if days_elapsed < offset:
            return None  # not due yet, and nothing later can be due either
        # This stage is due. But if there's an earlier, still-unresolved
        # stage awaiting approval, don't queue this one on top of it.
        return label

    return None
