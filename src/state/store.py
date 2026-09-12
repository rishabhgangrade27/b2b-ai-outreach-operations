"""Flat-file persistent state store.

This mirrors a real constraint from the production system this is derived
from: state is a single JSON document, written on every mutation, with no
external database. That's a deliberate simplicity trade-off for a
single-process automation tool, not an oversight - see docs/design-decisions.md
for the reasoning and its limits (no locking/atomicity across writes).
"""
from __future__ import annotations

import json
import os
import shutil
from typing import Any


class StateStore:
    def __init__(self, path: str = "state.json"):
        self.path = path
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if not os.path.exists(self.path):
            return {"contacts": {}, "sent_history": {}, "halted": []}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _flush(self) -> None:
        # Write to a temp file then move, so a crash mid-write can't leave
        # a truncated/corrupt state.json behind.
        tmp_path = f"{self.path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
        shutil.move(tmp_path, self.path)

    # --- contacts ---
    def known_emails(self) -> set[str]:
        return set(self._data["contacts"].keys())

    def upsert_contact(self, email: str, record: dict[str, Any]) -> None:
        self._data["contacts"][email] = record
        self._flush()

    def get_contact(self, email: str) -> dict[str, Any] | None:
        return self._data["contacts"].get(email)

    # --- sent history / cadence ---
    def record_sent(self, email: str, stage_label: str, sent_at: str) -> None:
        self._data["sent_history"].setdefault(email, []).append(
            {"stage_label": stage_label, "sent_at": sent_at}
        )
        self._flush()

    def sent_stages(self, email: str) -> list[str]:
        return [entry["stage_label"] for entry in self._data["sent_history"].get(email, [])]

    def sends_on_day(self, day_iso: str) -> int:
        count = 0
        for entries in self._data["sent_history"].values():
            count += sum(1 for e in entries if e["sent_at"].startswith(day_iso))
        return count

    # --- halt ---
    def halt(self, email: str) -> None:
        if email not in self._data["halted"]:
            self._data["halted"].append(email)
            self._flush()

    def is_halted(self, email: str) -> bool:
        return email in self._data["halted"]
