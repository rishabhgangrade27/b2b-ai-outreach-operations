"""State persistence: crash-safe writes and the operations built on top."""
import json

from src.state.store import StateStore


def test_new_state_file_starts_empty(tmp_path):
    state = StateStore(path=str(tmp_path / "state.json"))
    assert state.known_emails() == set()


def test_state_survives_reload(tmp_path):
    path = str(tmp_path / "state.json")
    StateStore(path=path).upsert_contact("a@example.com", {"stage": "sent"})
    reloaded = StateStore(path=path)
    assert reloaded.get_contact("a@example.com") == {"stage": "sent"}


def test_write_goes_through_a_temp_file_then_replace(tmp_path):
    path = tmp_path / "state.json"
    state = StateStore(path=str(path))
    state.upsert_contact("a@example.com", {"stage": "sent"})
    # No leftover temp file after a successful write.
    assert not (tmp_path / "state.json.tmp").exists()
    assert json.loads(path.read_text())["contacts"]["a@example.com"]["stage"] == "sent"


def test_sends_on_day_counts_only_that_day(tmp_path):
    state = StateStore(path=str(tmp_path / "state.json"))
    state.record_sent("a@example.com", "initial", "2026-01-05T10:00:00")
    state.record_sent("b@example.com", "initial", "2026-01-05T11:00:00")
    state.record_sent("c@example.com", "initial", "2026-01-06T09:00:00")
    assert state.sends_on_day("2026-01-05") == 2
    assert state.sends_on_day("2026-01-06") == 1
