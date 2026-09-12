# Safety controls

The core engineering claim of this project is that an AI-drafted message
cannot cause an external side effect on its own. Every control below exists
to make that true, not as decoration.

## Validation

A scraped contact only becomes an actionable target if its email passes
a format check and isn't a generic role address (`noreply@`, `webmaster@`,
etc). See `src/enrichment/validators.py`.

## Competitor filtering

A discovered business is checked against a blocklist before it can reach
the CRM or drafting stage. Deliberately a plain substring match, not a
fuzzy/semantic one - a blocklist a reviewer can read in ten seconds beats a
"smarter" filter nobody can audit. See `src/enrichment/competitor_filter.py`.

## Deduplication

A contact is dropped if it's already a CRM record, already tracked in local
state, or already appeared earlier in the same discovery run. Checked
against a single fully-paginated snapshot per run, not a per-candidate CRM
query. See `src/enrichment/dedup.py` and `docs/lessons-learned.md` for why
"fully paginated" specifically matters.

## Approval gating

No draft reaches the rate limiter or the email client without a human
explicitly approving it - a Slack reaction, not a bespoke UI. Rejecting a
draft doesn't just skip that one send, it halts the contact permanently.
See `src/approval/approval_flow.py`.

## Rate limiting

Even an approved draft doesn't send immediately. Three controls apply in
order: a warmup tier that raises the allowed daily volume gradually over
the first weeks of operation, a randomized (not fixed) daily cap within
that tier, and per-send jitter so a batch of approvals doesn't fire in the
same instant. See `src/rate_limiter/limiter.py`.

## Halt behavior

A contact can be removed from all future outreach - via an explicit
operator action or automatically on rejection - and that removal is
permanent: no cadence stage will ever fire for a halted contact again,
checked at the top of `due_followup_stage`. See
`src/cadence/followup_scheduler.py`.

## Retries and failure isolation

Background jobs run as named streams on independent schedules. One
stream's exception is caught and logged at that stream's boundary - it
never propagates to stop the scheduler or any other stream. See
`src/scheduler/job_runner.py`.

## State persistence

Approval state, send history, and halt status all survive a process
restart - state.json is the source of truth, not in-memory data. Writes go
to a temp file and are atomically moved into place, so a crash mid-write
can't corrupt the existing state. See `src/state/store.py`.

## DRY_RUN as an explicit boundary

Every integration that can cause a real external effect (`email_client`,
and in the real system also the CRM and Slack clients) takes a `dry_run`
flag through its call signature, not a global that's checked deep inside
some other function. That means a caller can never accidentally forget the
check - the check *is* the call.
