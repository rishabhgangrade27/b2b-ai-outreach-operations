"""Segment-specific outreach templates.

Templates are the default path for drafting - see drafting.py. Keeping a
template per segment (rather than asking the LLM to write every email from
scratch) keeps tone and structure consistent and cheap; the LLM is reserved
for cases the templates don't cover.
"""
from __future__ import annotations

TEMPLATES: dict[str, dict[str, str]] = {
    "segment_a": {
        "subject": "Quick question for {business_name}",
        "body": (
            "Hi team,\n\n"
            "Came across {business_name} while researching businesses in your area. "
            "We work with similar companies on {value_prop_a} - thought it might be "
            "relevant to what you're doing.\n\n"
            "Open to a short chat?\n\n"
            "Best,\nOutreach Team"
        ),
    },
    "segment_b": {
        "subject": "Thought this might be useful for {business_name}",
        "body": (
            "Hi there,\n\n"
            "Reaching out because {business_name} came up in our research on "
            "companies in your segment. We help teams like yours with {value_prop_b}.\n\n"
            "Worth 10 minutes?\n\n"
            "Best,\nOutreach Team"
        ),
    },
    "segment_c": {
        "subject": "For {business_name}",
        "body": (
            "Hi,\n\n"
            "Noticed {business_name} while looking into businesses in your space. "
            "We've helped similar companies with {value_prop_c}.\n\n"
            "Happy to share more if useful.\n\n"
            "Best,\nOutreach Team"
        ),
    },
}

_VALUE_PROPS = {
    "segment_a": "reducing manual admin overhead",
    "segment_b": "improving lead response time",
    "segment_c": "streamlining customer follow-up",
}


def render_template(segment_key: str, business_name: str) -> tuple[str, str]:
    template = TEMPLATES[segment_key]
    value_prop_key = f"value_prop_{segment_key.split('_')[-1]}"
    subject = template["subject"].format(business_name=business_name)
    body = template["body"].format(
        business_name=business_name, **{value_prop_key: _VALUE_PROPS[segment_key]}
    )
    return subject, body
