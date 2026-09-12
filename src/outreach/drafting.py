"""Draft generation: template-first, LLM fallback.

Templates cover the common case cheaply and predictably. The LLM path only
runs when a segment has no template (or for ad-hoc content requests outside
the core pipeline) - AI generation is the exception path, not the default,
which keeps output consistent and keeps LLM cost/latency out of the common
case.
"""
from __future__ import annotations

from src.integrations.llm_client import LLMClient
from src.models import Contact, Draft
from src.outreach.templates import TEMPLATES, render_template

_SYSTEM_PROMPT = (
    "You write short, plain, non-hypey B2B outreach emails. No emojis, "
    "no exclamation marks, no buzzwords. 4 sentences max."
)


def draft_initial_outreach(contact: Contact, llm_client: LLMClient) -> Draft:
    segment_key = contact.lead.segment_key
    if segment_key in TEMPLATES:
        subject, body = render_template(segment_key, contact.lead.business_name)
        return Draft(
            contact_email=contact.email or "",
            subject=subject,
            body=body,
            template_key=segment_key,
            generated_by="template",
            stage_label="initial",
        )

    body = llm_client.generate(
        _SYSTEM_PROMPT, f"Write an outreach email to {contact.lead.business_name}."
    )
    return Draft(
        contact_email=contact.email or "",
        subject=f"Quick question for {contact.lead.business_name}",
        body=body,
        template_key="llm_generated",
        generated_by="llm_fallback",
        stage_label="initial",
    )
