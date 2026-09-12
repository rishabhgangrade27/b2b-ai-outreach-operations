# Architecture

## System overview

```mermaid
flowchart TD
    A[Business search provider] --> B[Discovery pipeline]
    B --> C[Website contact extraction]
    C --> D[Validation]
    D --> E[Competitor filter]
    E --> F[Deduplication]
    F --> G[CRM]
    G --> H[Outreach drafting - template first, LLM fallback]
    H --> I[Slack human approval]
    I -- rejected --> J[Halt - permanent]
    I -- approved --> K[Rate limiter - warmup tier + daily cap + jitter]
    K --> L[Email delivery]
    L --> M[Persistent state]
    M --> N[Follow-up cadence scheduler]
    N -- due --> H
    N -- halted --> J
```

## Data flow: lead to sent email

```mermaid
sequenceDiagram
    participant Places as Search provider
    participant Disc as Discovery
    participant Enrich as Enrichment
    participant CRM
    participant LLM
    participant Slack
    participant Human
    participant RL as Rate limiter
    participant Email

    Places->>Disc: business result (name, website, phone)
    Disc->>Disc: extract email from website (mailto, then regex fallback)
    Disc->>Enrich: raw contact
    Enrich->>Enrich: validate + competitor filter + dedup
    Enrich->>CRM: create record (new contact only)
    CRM->>LLM: request draft
    LLM-->>CRM: subject + body (template-first, LLM fallback)
    CRM->>Slack: post draft for approval
    Slack->>Human: notify
    Human-->>Slack: react (approve / reject)
    Slack->>RL: approved draft
    RL->>RL: check warmup tier, daily cap, apply jitter
    RL->>Email: send (or hold for tomorrow if cap reached)
    Email->>CRM: record sent + timestamp in state
```

## Approval / send sequence (the safety-critical path)

```mermaid
sequenceDiagram
    participant Draft as AI-drafted email
    participant Slack
    participant Human
    participant State
    participant RL as Rate limiter
    participant Email

    Draft->>Slack: post for approval
    alt human approves
        Slack->>RL: approved
        RL->>RL: is today's cap already reached?
        alt cap reached
            RL->>State: leave pending, retry next cycle
        else capacity available
            RL->>RL: apply 15-45 min jitter
            RL->>Email: send
            Email->>State: record sent_at + stage
        end
    else human rejects
        Slack->>State: halt(contact) - permanent
        State-->>Draft: contact never re-enters cadence
    end
```

## Why this shape

The pipeline is linear on the happy path, but every stage that could produce
a false positive (a bad email, a competitor, a duplicate) sits *before* the
CRM write, and every stage that produces an external side effect (an actual
send) sits *after* a human approval and a rate-limit check. That ordering is
the whole design: cheap-to-reverse mistakes (a bad CRM record) are filtered
early; expensive-to-reverse mistakes (an email that already left the
building) are gated behind the two slowest, most deliberate steps in the
system.

## Module map

| Concern | Module |
|---|---|
| Lead discovery | `src/discovery/pipeline.py` |
| Contact extraction | `src/discovery/contact_extractor.py` |
| Validation | `src/enrichment/validators.py` |
| Competitor filtering | `src/enrichment/competitor_filter.py` |
| Deduplication | `src/enrichment/dedup.py` |
| CRM adapter | `src/integrations/crm_client.py` |
| Drafting | `src/outreach/drafting.py`, `src/outreach/templates.py` |
| LLM adapter | `src/integrations/llm_client.py` |
| Human approval | `src/approval/approval_flow.py` |
| Slack adapter | `src/integrations/slack_client.py` |
| Rate limiting | `src/rate_limiter/limiter.py` |
| Email adapter | `src/integrations/email_client.py` |
| Persistent state | `src/state/store.py` |
| Follow-up cadence | `src/cadence/followup_scheduler.py` |
| Background scheduling | `src/scheduler/job_runner.py` |
