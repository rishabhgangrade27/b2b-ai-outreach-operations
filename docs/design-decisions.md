# Design decisions

## Template-first, LLM-fallback drafting

Segment templates cover the common case. The LLM only drafts when a
segment has no template, or for ad-hoc content requests outside the core
pipeline. This keeps tone and structure predictable and keeps LLM latency/
cost off the hot path - generation is the exception, not the default.

## Flat-file state, not a database

State is a single `state.json`, read fully into memory on start and
rewritten (via temp-file-then-move) on every mutation. That's a deliberate
trade-off for a single-process automation tool with a low write volume, not
an oversight: it's simple to reason about, simple to inspect by hand, and
has no external moving parts to operate. Its known limit is that it doesn't
support concurrent writers - fine for one process, would need to change if
this became multi-worker.

## Substring blocklist over similarity matching for competitor filtering

A fuzzy or embedding-based "is this a competitor" check would catch more
edge cases, but nobody could look at it and immediately know why a business
was or wasn't filtered. A plain substring list is auditable in seconds by a
non-engineer, which matters more here than marginal recall.

## Approval via chat reaction, not a bespoke UI

The human approval step deliberately lives inside a tool the approver
already has open all day, rather than a dashboard that adds one more place
to check. The interface cost of building a UI didn't buy anything a
reaction-based approve/reject couldn't already do.

## Randomized rate caps and jitter, not a fixed daily limit

A fixed "N emails per day, sent back to back" pattern is itself a
detectable automation signature. A randomized cap within a tier, plus
per-send jitter, produces a more natural-looking (and, more importantly,
more gradual) sending pattern - this matters most in the early weeks of a
new sending identity's life.

## Distinguishing "the API failed" from "there's nothing here"

Every external client is written so a failed call returns a distinct
failure signal, never a value that looks the same as a genuinely empty
result. A caller that can't tell "the CRM timed out" from "the CRM board is
empty" will make the wrong decision on retry logic, on deduplication, and
on whether it's safe to proceed to a write. See `docs/lessons-learned.md`
for the incident that made this explicit.
