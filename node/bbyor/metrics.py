import json
import threading
import time
from contextlib import contextmanager
from pathlib import Path


class Metrics:
    """Appends one JSON line per timed operation (consumed by experiments/plot_metrics.py)."""

    def __init__(self, path: Path | None, node: str):
        self.path = path
        self.node = node
        self._lock = threading.Lock()

    @contextmanager
    def record(self, operation: str, round: int | None = None, **extra):
        start = time.perf_counter()
        try:
            yield
        finally:
            entry = {
                "timestamp": time.time(),
                "node": self.node,
                "operation": operation,
                "duration_ms": round_ms(time.perf_counter() - start),
            }
            if round is not None:
                entry["round"] = round
            entry.update(extra)
            self._append(entry)

    def _append(self, entry: dict) -> None:
        if self.path is None:
            return
        with self._lock, open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")


def round_ms(seconds: float) -> float:
    return round(seconds * 1000, 3)
