"""Background job runner.

Each named stream runs on its own interval. The important property: one
stream raising an exception must never take down the others, or the
process. A crash in, say, the discovery stream should not silently stop
the approval-polling stream from running too - each stream's body is
isolated so a bug in one job degrades only that job.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger("scheduler")


@dataclass
class Stream:
    name: str
    interval_seconds: int
    job: Callable[[], None]


def run_stream_once(stream: Stream) -> bool:
    """Runs one stream's job, isolating any exception. Returns True on
    success, False if the job raised (and was caught + logged)."""
    try:
        stream.job()
        return True
    except Exception:
        logger.exception("Stream %r raised - continuing other streams", stream.name)
        return False


def run_all_streams_once(streams: list[Stream]) -> dict[str, bool]:
    return {stream.name: run_stream_once(stream) for stream in streams}
