"""Shared data types used across the pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ApprovalState(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class LeadStage(Enum):
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    ENRICHED = "enriched"
    IN_CRM = "in_crm"
    DRAFTED = "drafted"
    AWAITING_APPROVAL = "awaiting_approval"
    SENT = "sent"
    HALTED = "halted"


@dataclass
class Lead:
    business_name: str
    website: str | None
    segment_key: str
    region_key: str
    source: str = "places_search"
    discovered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Contact:
    lead: Lead
    email: str | None
    phone: str | None
    extraction_method: str  # "mailto" | "regex_fallback" | "none"
    stage: LeadStage = LeadStage.DISCOVERED


@dataclass
class Draft:
    contact_email: str
    subject: str
    body: str
    template_key: str
    generated_by: str  # "template" | "llm_fallback"
    stage_label: str  # "initial" | "followup_day4" | "followup_week2"


@dataclass
class ApprovalRequest:
    draft: Draft
    state: ApprovalState = ApprovalState.PENDING
    requested_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved_at: str | None = None
