"""Append-only audit trail. Kept in memory for fast reads and written through to SingleStore
when it is configured."""

import itertools
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable

_events: list[dict[str, Any]] = []
_lock = threading.Lock()
_ids = itertools.count(1)
_sinks: list[Callable[[dict[str, Any]], None]] = []


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def add_sink(sink: Callable[[dict[str, Any]], None]) -> None:
    _sinks.append(sink)


def log(run_id: str, step: str, actor: str, model: str | None = None,
        latency_ms: int | None = None, **detail: Any) -> dict[str, Any]:
    event = {
        "id": next(_ids),
        "run_id": run_id,
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "step": step,
        "actor": actor,
        "model": model,
        "latency_ms": latency_ms,
        "detail": detail,
    }
    with _lock:
        _events.append(event)
    for sink in _sinks:
        try:
            sink(event)
        except Exception as exc:  # a failing sink must never break the request
            print(f"[audit] sink failed: {exc}")
    return event


def events(run_id: str) -> list[dict[str, Any]]:
    with _lock:
        return [e for e in _events if e["run_id"] == run_id]


@contextmanager
def timer():
    start = time.perf_counter()
    box: dict[str, float] = {"start": start}
    try:
        yield box
    finally:
        box["ms"] = int((time.perf_counter() - start) * 1000)


def since(box: dict) -> int:
    return int((time.perf_counter() - box["start"]) * 1000)
