import random

from src.rate_limiter.limiter import can_send_today, current_tier_range, daily_cap, jitter_minutes

TIERS = ((0, 10, 20), (7, 20, 30), (14, 30, 40), (21, 50, 70))


def test_tier_selection_by_day():
    assert current_tier_range(0, TIERS) == (10, 20)
    assert current_tier_range(6, TIERS) == (10, 20)
    assert current_tier_range(7, TIERS) == (20, 30)
    assert current_tier_range(20, TIERS) == (30, 40)
    assert current_tier_range(100, TIERS) == (50, 70)


def test_daily_cap_stays_within_tier_bounds():
    rng = random.Random(42)
    for day in (0, 5, 7, 15, 25):
        lo, hi = current_tier_range(day, TIERS)
        for _ in range(200):
            cap = daily_cap(day, TIERS, rng)
            assert lo <= cap <= hi


def test_daily_cap_is_low_biased_not_fixed():
    rng = random.Random(1)
    caps = [daily_cap(0, TIERS, rng) for _ in range(500)]
    assert len(set(caps)) > 1  # not hitting the same number every time
    assert sum(caps) / len(caps) < 15  # triangular distribution favors the lower end of (10, 20)


def test_jitter_within_configured_bounds():
    rng = random.Random(2)
    for _ in range(200):
        minutes = jitter_minutes((15, 45), rng)
        assert 15 <= minutes <= 45


def test_can_send_today_respects_cap():
    rng = random.Random(3)
    cap = daily_cap(0, TIERS, random.Random(3))
    assert can_send_today(cap - 1, 0, TIERS, random.Random(3)) is True
    assert can_send_today(cap, 0, TIERS, random.Random(3)) is False
