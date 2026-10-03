"""
Shared TTL cache used by both the driver-grades and race-summary caches.

The important property beyond the TTL is single-flight: only one thread ever
runs the (slow, upstream/LLM-bound) compute for a given cache, and everyone
else waits for its result. Without that, a single page load fired two full
pipelines — React StrictMode mounts effects twice in dev, so the frontend
issues two identical requests, and each used to miss the cache independently.
"""
import logging
import threading
import time
from typing import Callable

logger = logging.getLogger("f1_driver_grades")


class TTLCache:
    def __init__(self, compute: Callable[[int], dict], ttl_seconds: float, name: str = "cache"):
        self._compute = compute
        self._name = name
        self._ttl = ttl_seconds
        self._state_lock = threading.Lock()
        self._compute_lock = threading.Lock()
        self._data: dict | None = None
        self._computed_at: float | None = None

    def _read(self) -> tuple[dict | None, float | None]:
        with self._state_lock:
            return self._data, self._computed_at

    def _compute_and_store(self, season: int, *, newer_than: float | None = None) -> dict:
        # Single-flight: whoever gets the lock computes; anyone who was
        # waiting on it takes the result that landed while they waited
        # rather than repeating the work.
        with self._compute_lock:
            data, computed_at = self._read()
            if data is not None and computed_at is not None:
                is_fresh_enough = (
                    computed_at > newer_than
                    if newer_than is not None
                    else (time.monotonic() - computed_at) < self._ttl
                )
                if is_fresh_enough:
                    return data

            data = self._compute(season)
            with self._state_lock:
                self._data = data
                self._computed_at = time.monotonic()
            return data

    def get_or_compute(self, season: int) -> dict:
        data, computed_at = self._read()
        is_stale = computed_at is None or (time.monotonic() - computed_at) >= self._ttl
        if data is None or is_stale:
            return self._compute_and_store(season)
        return data

    def force_refresh(self, season: int) -> dict:
        # A refresh must not serve the value it was asked to replace, but two
        # near-simultaneous refreshes should still only recompute once — so
        # accept any result computed after this call started.
        return self._compute_and_store(season, newer_than=time.monotonic())

    def try_warm(self, season: int) -> None:
        """Best-effort warm for startup: the app must still boot if the
        upstream API or the narrative call is failing.

        Swallowing the error is deliberate; swallowing it *silently* was a
        mistake. A warm that fails leaves the cache empty, so the first
        visitor pays the full pipeline — the exact symptom the warm exists to
        remove — and with no log line there was nothing to distinguish "the
        warm failed" from "the warm was never reached". Log it.
        """
        started = time.monotonic()
        try:
            self.get_or_compute(season)
        except Exception as exc:
            logger.warning(
                "Startup warm of %s failed after %.1fs (%s: %s). The cache is "
                "empty, so the first request will compute it instead.",
                self._name, time.monotonic() - started, type(exc).__name__, exc,
            )
            return
        logger.info("Startup warm of %s finished in %.1fs", self._name, time.monotonic() - started)
