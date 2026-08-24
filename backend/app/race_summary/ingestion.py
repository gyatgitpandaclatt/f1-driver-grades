"""
Fetch a single race's results, lap times, and pit stops from the Jolpica/Ergast
API (the same provider the rest of this app already uses). Unlike FastF1, this
has no telemetry, tire compound, weather, or race-control data -- see
race_summary/README notes in pipeline.py for what that means for the narrative.
"""
import threading
import time

from ..config import (
    API_BASE_URL,
    INCOMPLETE_ROUND_CACHE_TTL_SECONDS,
    PAGE_LIMIT,
    ROUND_CACHE_MAX_ROUNDS,
)
from ..data_fetch import _get_json
from ..exceptions import RaceSessionNotAvailableError, UpstreamAPIError

# Raw per-round payloads, keyed by (season, round). Values are
# (expires_at, data) where expires_at is None for "never" — a completed
# race's results, laps, and pit stops are immutable once published, so the
# only entries that expire are rounds whose lap data hasn't landed yet.
#
# This is per-process state: it's correct under uvicorn's default single
# worker (what start.sh and the Dockerfile run). If this ever scales to
# multiple workers, back it with Redis or SQLite instead — an in-memory
# dict is duplicated per worker, multiplying upstream calls by the worker
# count.
_round_cache: dict[tuple[int, int], tuple[float | None, dict]] = {}
_round_cache_lock = threading.Lock()


def _cache_get(key: tuple[int, int]) -> dict | None:
    with _round_cache_lock:
        entry = _round_cache.get(key)
        if entry is None:
            return None
        expires_at, data = entry
        if expires_at is not None and time.monotonic() >= expires_at:
            del _round_cache[key]
            return None
        return data


def _cache_put(key: tuple[int, int], data: dict, *, permanent: bool) -> None:
    expires_at = None if permanent else time.monotonic() + INCOMPLETE_ROUND_CACHE_TTL_SECONDS
    with _round_cache_lock:
        _round_cache[key] = (expires_at, data)
        # Bound memory: keep only the most recent rounds (a season is ~24).
        while len(_round_cache) > ROUND_CACHE_MAX_ROUNDS:
            del _round_cache[min(_round_cache)]


def _laps_look_complete(laps: list[dict]) -> bool:
    """Whether a round's lap data is a full, gapless 1..N run.

    Guards the permanent cache: a truncated fetch (a page that came back
    short, a partially published race) must not be stored forever, and a gap
    also breaks lap-over-lap comparisons downstream.
    """
    if not laps:
        return False
    numbers = sorted(int(lap["number"]) for lap in laps)
    return numbers == list(range(1, numbers[-1] + 1))


def fetch_race_data(season: int, round_number: int) -> dict:
    """Everything the summarizer needs for one round, cached.

    Returns {"event": ..., "laps": [...], "pit_stops": [...]}. A round that
    came back with lap data is complete and cached permanently; one without
    laps yet (results published, timing data still to come) is cached only
    briefly so the next visit picks up the full set.
    """
    key = (int(season), int(round_number))
    cached = _cache_get(key)
    if cached is not None:
        return cached

    data = {
        "event": fetch_race_event(season, round_number),
        "laps": fetch_laps(season, round_number),
        "pit_stops": fetch_pit_stops(season, round_number),
    }
    _cache_put(key, data, permanent=_laps_look_complete(data["laps"]))
    return data


def fetch_race_event(season: int, round_number: int) -> dict:
    """
    The race's results.json payload: raceName, date, and Results[] (grid,
    finish position, status, points, driver/constructor info). This is also
    where we get the driverId -> 3-letter code mapping used to join laps and
    pit stops (those endpoints only give driverId, not code).
    """
    url = f"{API_BASE_URL}/{season}/{round_number}/results.json?limit=30"
    data = _get_json(url)
    try:
        races = data["MRData"]["RaceTable"]["Races"]
    except KeyError as exc:
        raise UpstreamAPIError(f"Unexpected response shape from {url}: {exc}") from exc

    if not races:
        raise RaceSessionNotAvailableError(
            f"No classified results yet for {season} round {round_number}."
        )
    return races[0]


def fetch_laps(season: int, round_number: int) -> list[dict]:
    """
    Returns Ergast's Laps list: [{"number": "1", "Timings": [{"driverId":
    ..., "time": "1:32.190", "position": "1"}, ...]}, ...].

    limit/offset here paginate over individual driver-lap timing rows, not
    whole laps -- a single lap's Timings routinely split across two pages
    (confirmed against live data), so pages must be merged by lap number,
    not concatenated.
    """
    laps_by_number: dict[int, list[dict]] = {}
    collected = 0
    expected: int | None = None
    offset = 0
    while True:
        url = f"{API_BASE_URL}/{season}/{round_number}/laps.json?limit={PAGE_LIMIT}&offset={offset}"
        data = _get_json(url)
        try:
            mrdata = data["MRData"]
            total = int(mrdata["total"])
            races = mrdata["RaceTable"]["Races"]
        except (KeyError, ValueError) as exc:
            raise UpstreamAPIError(f"Unexpected response shape from {url}: {exc}") from exc

        expected = total
        if not races:
            break
        received = 0
        for lap in races[0]["Laps"]:
            lap_number = int(lap["number"])
            timings = lap["Timings"]
            laps_by_number.setdefault(lap_number, []).extend(timings)
            received += len(timings)
        collected += received

        # Advance by what came back, never by what we asked for: the provider
        # caps `limit` at its own maximum and silently returns a smaller page,
        # so striding by PAGE_LIMIT would skip every row in between.
        if received == 0:
            break
        offset += received
        if offset >= total:
            break

    # A run that ends with fewer rows than the provider said exist is a
    # truncated fetch, not a short race. Fail rather than return it: the
    # caller would otherwise cache the partial result permanently, and a
    # missing stretch of laps silently distorts every downstream metric.
    if expected is not None and collected < expected:
        raise UpstreamAPIError(
            f"Incomplete lap data for {season} round {round_number}: "
            f"got {collected} of {expected} timing rows."
        )

    return [
        {"number": str(number), "Timings": timings}
        for number, timings in sorted(laps_by_number.items())
    ]


def fetch_pit_stops(season: int, round_number: int) -> list[dict]:
    """
    Returns Ergast's PitStops list: [{"driverId": ..., "lap": "8", "stop":
    "1", "time": "15:15:19", "duration": "21.789"}, ...]. Each entry is
    self-contained (no cross-page splitting like laps.json).
    """
    all_stops: list[dict] = []
    offset = 0
    while True:
        url = f"{API_BASE_URL}/{season}/{round_number}/pitstops.json?limit={PAGE_LIMIT}&offset={offset}"
        data = _get_json(url)
        try:
            mrdata = data["MRData"]
            total = int(mrdata["total"])
            races = mrdata["RaceTable"]["Races"]
        except (KeyError, ValueError) as exc:
            raise UpstreamAPIError(f"Unexpected response shape from {url}: {exc}") from exc

        if not races:
            break
        stops = races[0]["PitStops"]
        all_stops.extend(stops)

        if not stops:  # see fetch_laps: stride by rows received, not requested
            break
        offset += len(stops)
        if offset >= total:
            break

    return all_stops
