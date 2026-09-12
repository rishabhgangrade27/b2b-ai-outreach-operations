# Running the demo

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

No `.env` file or API keys are required - the demo runs entirely against
mock integrations (`src/integrations/*`, the `Mock*` classes).

## Run it

```bash
python demo.py
```

This walks five synthetic businesses through the full pipeline: discovery,
extraction (including a deliberately malformed contact page, to show the
extraction fallback recovering a clean email from a phone number glued
against it with no separator), validation, competitor filtering, dedup,
CRM record creation, drafting, a simulated Slack approval (one contact is
rejected on purpose, to show the halt behavior), rate-limiter checks, a
dry-run send, and the resulting follow-up state.

It uses a fixed random seed, so the output is reproducible run to run.

## Run the tests

```bash
python -m pytest -v
```

Covers: rate limiter tier/jitter/cap behavior, the email-extraction
regression, competitor filtering, deduplication, halt/cadence rules,
approval-flow state transitions, and state-store persistence/atomicity.

## What's mocked vs what's structurally real

Every integration (`llm_client`, `email_client`, `slack_client`,
`crm_client`, `places_client`) defines the real interface plus a `Mock*`
implementation. The business logic that sits on top of those interfaces
(discovery orchestration, validation, dedup, drafting, approval, rate
limiting, cadence, scheduling) is the actual reconstructed logic from the
production system - it's the integration *clients* that are swapped for
mocks, not the decisions made around them.
