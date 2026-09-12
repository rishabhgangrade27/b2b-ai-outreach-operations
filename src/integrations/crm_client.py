"""CRM integration - lead/contact system of record.

Modeled on a paginated GraphQL-style board API. The pagination detail here
matters: a real production bug in the system this is derived from came from
a CRM API that silently caps results per page - callers that don't follow
the `cursor` field will believe a board has fewer records than it really
does, and re-process/re-create items that already exist. See
docs/lessons-learned.md.
"""
from __future__ import annotations

from typing import Protocol


class CRMClient(Protocol):
    def get_all_items(self, board_id: str) -> list[dict]: ...
    def create_item(self, board_id: str, column_values: dict) -> str: ...
    def update_item(self, item_id: str, column_values: dict) -> None: ...


class MockCRMClient:
    """In-memory CRM that deliberately paginates in small pages, to exercise
    the same "did you follow the cursor" code path a real board API forces.
    """

    def __init__(self, page_size: int = 3):
        self._items: dict[str, dict] = {}
        self._next_id = 1
        self.page_size = page_size

    def get_all_items(self, board_id: str) -> list[dict]:
        # Simulates cursor-based pagination under the hood; the interface
        # only ever hands back the fully-paginated result so pipeline code
        # is written against the *complete* set, never a partial page.
        all_items = list(self._items.values())
        pages = [all_items[i : i + self.page_size] for i in range(0, len(all_items), self.page_size)]
        combined: list[dict] = []
        for page in pages:
            combined.extend(page)
        return combined

    def create_item(self, board_id: str, column_values: dict) -> str:
        item_id = str(self._next_id)
        self._next_id += 1
        self._items[item_id] = {"id": item_id, **column_values}
        return item_id

    def update_item(self, item_id: str, column_values: dict) -> None:
        if item_id in self._items:
            self._items[item_id].update(column_values)
