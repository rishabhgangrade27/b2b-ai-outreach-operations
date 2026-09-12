"""Central configuration, loaded from environment variables.

Nothing sensitive is hardcoded here - board IDs, channel IDs, and API keys
are all env-driven so the same code runs against real or mock integrations
depending on what's configured.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _bool_env(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Segment:
    """A target customer segment - drives which outreach template is used."""
    key: str
    label: str
    search_terms: list[str]


@dataclass(frozen=True)
class Region:
    key: str
    label: str


@dataclass(frozen=True)
class Settings:
    dry_run: bool = field(default_factory=lambda: _bool_env("DRY_RUN", True))

    # Discovery
    max_pages_per_search: int = 2
    segments: tuple[Segment, ...] = (
        Segment("segment_a", "Segment A", ["segment a service provider"]),
        Segment("segment_b", "Segment B", ["segment b service provider"]),
        Segment("segment_c", "Segment C", ["segment c service provider"]),
    )
    regions: tuple[Region, ...] = (
        Region("region_1", "Region 1"),
        Region("region_2", "Region 2"),
        Region("region_3", "Region 3"),
    )
    competitor_name_substrings: tuple[str, ...] = (
        "our own company",
    )

    # Rate limiting / warmup (days since first send -> (min, max) sends/day)
    warmup_tiers: tuple[tuple[int, int, int], ...] = (
        (0, 10, 20),
        (7, 20, 30),
        (14, 30, 40),
        (21, 50, 70),
    )
    min_gap_between_sends_minutes: tuple[int, int] = (2, 6)
    pre_send_jitter_minutes: tuple[int, int] = (15, 45)

    # Cadence
    followup_day_offsets: tuple[int, ...] = (4, 14)  # Day 4, Week 2

    # Email
    email_from: str = field(default_factory=lambda: os.getenv("EMAIL_FROM_ADDRESS", "outreach@example.com"))
    email_bcc: str | None = field(default_factory=lambda: os.getenv("EMAIL_BCC_ADDRESS") or None)

    # State
    state_file_path: str = "state.json"


SETTINGS = Settings()
