from datetime import date

from src.cadence.followup_scheduler import due_followup_stage
from src.state.store import StateStore

OFFSETS = (4, 14)


def test_no_followup_due_before_day_4(tmp_path):
    state = StateStore(path=str(tmp_path / "state.json"))
    result = due_followup_stage(date(2026, 1, 1), date(2026, 1, 3), "a@example.com", state, OFFSETS)
    assert result is None


def test_day_4_followup_becomes_due(tmp_path):
    state = StateStore(path=str(tmp_path / "state.json"))
    result = due_followup_stage(date(2026, 1, 1), date(2026, 1, 5), "a@example.com", state, OFFSETS)
    assert result == "followup_day4"


def test_week_2_followup_not_due_until_day_4_recorded(tmp_path):
    state = StateStore(path=str(tmp_path / "state.json"))
    state.record_sent("a@example.com", "followup_day4", "2026-01-05")
    result = due_followup_stage(date(2026, 1, 1), date(2026, 1, 15), "a@example.com", state, OFFSETS)
    assert result == "followup_week2"


def test_halted_contact_never_gets_a_followup(tmp_path):
    state = StateStore(path=str(tmp_path / "state.json"))
    state.halt("a@example.com")
    result = due_followup_stage(date(2026, 1, 1), date(2026, 2, 1), "a@example.com", state, OFFSETS)
    assert result is None


def test_halt_is_permanent_even_after_being_recorded_as_sent(tmp_path):
    state = StateStore(path=str(tmp_path / "state.json"))
    state.record_sent("a@example.com", "initial", "2026-01-01")
    state.halt("a@example.com")
    assert state.is_halted("a@example.com") is True
    result = due_followup_stage(date(2026, 1, 1), date(2026, 1, 20), "a@example.com", state, OFFSETS)
    assert result is None
