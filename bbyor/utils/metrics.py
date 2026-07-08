import json
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path

_lock = threading.Lock()
_metrics_path = Path(os.getenv("METRICS_FILE", "./metrics.jsonl"))


@contextmanager
def record(operation: str, _round: int = None, **extra):
    """Time a block and append a JSONL entry to the metrics file.

    Usage:
        with metrics.record("fhe_encrypt", _round=r):
            result = encrypt(value)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1_000
        _node = os.getenv("PUBLIC_DID", "unknown")
        entry: dict = {
            "timestamp": time.time(),
            "node": _node,
            "operation": operation,
            "duration_ms": round(duration_ms, 3),
        }
        if _round is not None:
            entry["round"] = _round
        entry.update(extra)
        _append(entry)


def _append(entry: dict) -> None:
    with _lock:
        with open(_metrics_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
