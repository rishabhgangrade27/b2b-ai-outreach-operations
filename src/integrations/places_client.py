"""Business-search / lead-discovery provider.

Modeled on a text-search Places-style API: search by term + region, get back
a page of businesses, follow the next-page token up to a configured limit.
"""
from __future__ import annotations

from typing import Protocol


class PlacesClient(Protocol):
    def search(self, query: str, region: str, max_pages: int) -> list[dict]: ...


class MockPlacesClient:
    """Returns a fixed, small synthetic result set - enough to demonstrate
    pagination and per-region/segment iteration without a real API key.
    """

    def __init__(self, fixture: list[dict]):
        self._fixture = fixture

    def search(self, query: str, region: str, max_pages: int) -> list[dict]:
        return [
            r
            for r in self._fixture
            if r["region_key"] == region and query in r.get("matched_segments", [])
        ]
