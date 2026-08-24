import logging
import math
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests
import pandas as pd

from .config import (
    API_BASE_URL,
    DEFAULT_RETRY_AFTER_SECONDS,
    MAX_RETRY_AFTER_SECONDS,
    MAX_RETRY_SLEEP_SECONDS,
    MAX_UPSTREAM_RETRIES,
    PAGE_LIMIT,
    REQUEST_TIMEOUT,
    UPSTREAM_BACKOFF_BASE_SECONDS,
    UPSTREAM_MAX_CONCURRENCY,
)
from .exceptions import UpstreamAPIError, UpstreamRateLimitedError

logger = logging.getLogger("f1_driver_grades")

# One pooled session for every upstream call: the pipelines fire a run of
# sequential requests against a single host, so reusing the TCP/TLS
# connection removes a full handshake per page.
_session = requests.Session()

# Requests run in FastAPI's threadpool, so several can be in flight at once
# (e.g. a driver-grades warm and a race-summary build). Cap the concurrency
# we aim at the provider so we stay under its burst limit.
_concurrency = threading.Semaphore(UPSTREAM_MAX_CONCURRENCY)


def _http_date_delay(raw: str) -> float | None:
    """Seconds until an HTTP-date, or None if `raw` isn't one."""
    try:
        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:  # a date without a zone is UTC per RFC 9110
        when = when.replace(tzinfo=timezone.utc)
    return (when - datetime.now(timezone.utc)).total_seconds()


def _retry_after_seconds(response: requests.Response) -> int:
    """Parse Retry-After, which RFC 9110 allows in either form: delay-seconds
    or an HTTP-date.

    The value comes from the provider, so it is not trusted: anything
    unparseable, non-finite (inf/NaN — int() raises OverflowError on those),
    or absurdly large falls back to, or is clamped to, our own bounds.
    """
    raw = response.headers.get("Retry-After", "")

    try:
        seconds: float | None = float(raw)
    except (TypeError, ValueError):
        seconds = _http_date_delay(raw)

    if seconds is None or not math.isfinite(seconds):
        return DEFAULT_RETRY_AFTER_SECONDS
    return int(min(max(1.0, seconds), MAX_RETRY_AFTER_SECONDS))


def _get_json(url: str) -> dict:
    """GET a JSON payload, retrying transient upstream failures.

    429s and 5xx are retried with exponential backoff (honouring Retry-After
    when the provider sends one). A 429 that outlives the retries raises
    UpstreamRateLimitedError so the API edge can answer 503 + Retry-After
    rather than a misleading 502.
    """
    last_exc: Exception | None = None

    for attempt in range(MAX_UPSTREAM_RETRIES + 1):
        is_last = attempt == MAX_UPSTREAM_RETRIES
        try:
            with _concurrency:
                r = _session.get(url, timeout=REQUEST_TIMEOUT)

            if r.status_code == 429:
                retry_after = _retry_after_seconds(r)
                # Wait it out in-process only if the wait is short. A long
                # one belongs to the client: holding the request open for it
                # burns a worker thread and outlives proxy timeouts anyway.
                if is_last or retry_after > MAX_RETRY_SLEEP_SECONDS:
                    raise UpstreamRateLimitedError(
                        f"Rate limited by the F1 data provider on {url}.",
                        retry_after=retry_after,
                    )
                logger.info("429 from %s; retrying in %ss", url, retry_after)
                time.sleep(retry_after)
                continue

            if r.status_code >= 500 and not is_last:
                delay = UPSTREAM_BACKOFF_BASE_SECONDS * (2 ** attempt)
                logger.info("%s from %s; retrying in %ss", r.status_code, url, delay)
                time.sleep(delay)
                continue

            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as exc:
            last_exc = exc
            if is_last:
                break
            time.sleep(UPSTREAM_BACKOFF_BASE_SECONDS * (2 ** attempt))

    raise UpstreamAPIError(f"Failed to fetch {url}: {last_exc}") from last_exc


# The per-race list key varies by endpoint; a race payload carries exactly one.
RESULT_KEYS = ("Results", "QualifyingResults")


def _paginate_races(endpoint: str, season: int):
    offset = 0
    all_races = []
    while True:
        url = f"{API_BASE_URL}/{season}/{endpoint}.json?limit={PAGE_LIMIT}&offset={offset}"
        data = _get_json(url)
        try:
            mrdata = data["MRData"]
            total = int(mrdata["total"])
            races = mrdata["RaceTable"]["Races"]
        except (KeyError, ValueError) as exc:
            raise UpstreamAPIError(f"Unexpected response shape from {url}: {exc}") from exc

        all_races.extend(races)

        # `total` counts result rows, not races, so stride by the rows this
        # page actually returned — the provider may cap `limit` below what we
        # asked for, and striding by PAGE_LIMIT would skip the difference.
        received = sum(len(race.get(key, [])) for race in races for key in RESULT_KEYS)
        if received == 0:
            break
        offset += received
        if offset >= total:
            break
    return all_races


def fetch_qualifying_results(season: int) -> pd.DataFrame:
    rows = []
    for race in _paginate_races("qualifying", season):
        round_num = int(race["round"])
        race_name = race["raceName"]

        for q in race["QualifyingResults"]:
            driver = q["Driver"]
            constructor = q["Constructor"]

            rows.append({
                "season": season,
                "round": round_num,
                "race_name": race_name,
                "driver_code": driver.get("code", ""),
                "driver": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                "constructor": constructor.get("name", ""),
                "qual_pos": int(q["position"]),
                "got_pole": 1 if q["position"] == "1" else 0,
            })

    return pd.DataFrame(rows)


def fetch_race_results(season: int) -> pd.DataFrame:
    rows = []
    for race in _paginate_races("results", season):
        round_num = int(race["round"])
        race_name = race["raceName"]

        for res in race["Results"]:
            driver = res["Driver"]
            constructor = res["Constructor"]
            pos_text = res.get("positionText", "")

            is_classified = pos_text.lstrip("-").isdigit()
            finish_pos = int(res["position"]) if is_classified else None
            dnf = 0 if is_classified else 1

            rows.append({
                "season": season,
                "round": round_num,
                "race_name": race_name,
                "driver_code": driver.get("code", ""),
                "driver": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                "constructor": constructor.get("name", ""),
                "grid_pos": int(res["grid"]) if res["grid"].isdigit() else None,
                "finish_pos": finish_pos,
                "position_text": pos_text,
                "points_scored": float(res["points"]),
                "got_win": 1 if pos_text == "1" else 0,
                "dnf": dnf,
            })

    return pd.DataFrame(rows)


def fetch_driver_standings(season: int) -> pd.DataFrame:
    url = f"{API_BASE_URL}/{season}/driverStandings.json"
    data = _get_json(url)

    try:
        standings_list = data["MRData"]["StandingsTable"]["StandingsLists"]
    except KeyError as exc:
        raise UpstreamAPIError(f"Unexpected response shape from {url}: {exc}") from exc

    if not standings_list:
        return pd.DataFrame(columns=[
            "Position", "Driver", "Driver Code", "Nationality",
            "Constructor", "Points", "Wins",
        ])

    standings = standings_list[0]["DriverStandings"]

    rows = []
    for entry in standings:
        driver = entry["Driver"]
        constructor = entry["Constructors"][0] if entry["Constructors"] else {}
        rows.append({
            "Position": int(entry["position"]),
            "Driver": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
            "Driver Code": driver.get("code", ""),
            "Nationality": driver.get("nationality", ""),
            "Constructor": constructor.get("name", ""),
            "Points": float(entry["points"]),
            "Wins": int(entry["wins"]),
        })

    return pd.DataFrame(rows).sort_values("Position").reset_index(drop=True)
