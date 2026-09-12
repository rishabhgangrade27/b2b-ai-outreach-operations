"""Send-rate control: warmup tiers, a randomized daily cap, and per-send
jitter.

The point of this module is that an approved draft does not fire the moment
it's approved. Three separate controls sit between "approved" and "sent":

  1. Warmup tiers - the allowed daily volume increases in steps over the
     first few weeks of operation, rather than starting at full volume from
     day one. New sending identities that ramp up gradually are treated
     more favorably by receiving mail systems than ones that start at full
     volume immediately.
  2. A randomized (not fixed) daily cap within the current tier's range,
     biased toward the lower end - so send volume varies day to day instead
     of hitting the exact same number every time, which itself looks
     automated.
  3. Per-send jitter - a random delay before an approved send actually
     fires, so a batch of approvals doesn't all go out in the same second.
"""
from __future__ import annotations

import random
from datetime import date, timedelta


def current_tier_range(days_since_start: int, tiers: tuple[tuple[int, int, int], ...]) -> tuple[int, int]:
    """tiers: sequence of (day_offset, min, max), sorted ascending by day_offset."""
    applicable = [(min_, max_) for offset, min_, max_ in tiers if days_since_start >= offset]
    if not applicable:
        return tiers[0][1], tiers[0][2]
    return applicable[-1]


def daily_cap(days_since_start: int, tiers: tuple[tuple[int, int, int], ...], rng: random.Random | None = None) -> int:
    rng = rng or random
    lo, hi = current_tier_range(days_since_start, tiers)
    # Low-biased triangular distribution: most days land closer to the
    # floor of the tier, occasional days reach toward the ceiling.
    return round(rng.triangular(lo, hi, lo))


def jitter_minutes(bounds: tuple[int, int], rng: random.Random | None = None) -> int:
    rng = rng or random
    lo, hi = bounds
    return rng.randint(lo, hi)


def can_send_today(sends_today: int, days_since_start: int, tiers: tuple[tuple[int, int, int], ...], rng: random.Random | None = None) -> bool:
    return sends_today < daily_cap(days_since_start, tiers, rng)


def days_since(start_date: date, today: date) -> int:
    return (today - start_date).days
