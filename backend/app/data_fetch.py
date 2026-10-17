import functools
import logging
import math
import re
import threading
import time
import unicodedata
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests
import pandas as pd

from .config import (
    API_BASE_URL,
    DEFAULT_RETRY_AFTER_SECONDS,
    FIRST_CONSTRUCTORS_SEASON,
    FIRST_CHAMPIONSHIP_SEASON,
    FIRST_SPRINT_SEASON,
    MAX_RETRY_AFTER_SECONDS,
    MAX_RETRY_SLEEP_SECONDS,
    MAX_UPSTREAM_RETRIES,
    PAGE_LIMIT,
    REQUEST_TIMEOUT,
    UPSTREAM_BACKOFF_BASE_SECONDS,
    UPSTREAM_MAX_CONCURRENCY,
    is_completed_season,
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


# A finished season's fetches, keyed by (fetcher, season). Its results never
# change, and the grades and the season summary for the same season both
# need them, so each is fetched once per process and shared. The current
# season is always fetched fresh: its callers' own caches decide how fresh.
#
# Per-process state, like race_summary/ingestion.py's round cache: fine under
# the single uvicorn worker start.sh and the Dockerfile run.
_completed_season_data: dict[tuple[str, int], pd.DataFrame] = {}
_completed_season_locks: dict[tuple[str, int], threading.Lock] = {}
_completed_season_guard = threading.Lock()


def _shared_once_completed(fetch):
    @functools.wraps(fetch)
    def wrapper(season: int) -> pd.DataFrame:
        if not is_completed_season(season):
            return fetch(season)
        key = (fetch.__name__, int(season))
        with _completed_season_guard:
            lock = _completed_season_locks.setdefault(key, threading.Lock())
        # Per key, so the grades and the summary opening the same season at
        # once share one fetch instead of racing each other upstream.
        with lock:
            data = _completed_season_data.get(key)
            if data is None:
                data = fetch(season)
                # An empty answer for a finished season means the provider
                # had a bad moment, not that the season had no races.
                if data.empty:
                    return data
                _completed_season_data[key] = data
        # Callers are free to modify what they get back.
        return data.copy()
    return wrapper


# Three-letter driver codes. The whole app keys a season's drivers by code,
# but Ergast only has one for drivers from about the 2000s on; most before
# them have none. A driver without one gets one made up from their surname,
# unique within the season — the same scheme the broadcasts use, so Fangio
# is FAN — and a code two drivers share in one season is kept by the first
# and remade for the other. A season's codes are
# settled from its race results, and every other fetch for the season reads
# them from there, so the same driver has the same code on every page.
#
# Per-process state, like _completed_season_data below.
_season_codes: dict[int, dict[str, str]] = {}
_season_codes_guard = threading.Lock()

# Every (round, driverId) entered in a season, starters or not. The results
# drop entrants who failed to qualify, but "did they take part in this
# round at all" still needs them: a regular who failed to qualify was not
# replaced by whoever raced that day.
_season_entrants: dict[int, set[tuple[int, str]]] = {}


def was_entered(season: int, round_number: int, driver_id: str) -> bool:
    """Whether the driver was entered in the round, started or not."""
    if season not in _season_entrants:
        fetch_race_results(season)
    return (int(round_number), driver_id) in _season_entrants.get(season, set())


def _letters(text: str) -> str:
    """"Pérez" -> "PEREZ": accents folded, everything but A-Z dropped."""
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z]", "", folded.upper())


def _code_candidates(driver: dict):
    """Codes to try for a driver without one of their own, best first."""
    words = driver.get("familyName", "").split()
    # "von Trips" -> Trips, "de Graffenried" -> Graffenried: the particle
    # isn't what anyone would abbreviate.
    while len(words) > 1 and words[0][:1].islower():
        words = words[1:]
    family = _letters(" ".join(words)) or _letters(driver.get("driverId", ""))
    given = _letters(driver.get("givenName", ""))
    family = (family + given + "XXX")[: max(3, len(family))]
    yield family[:3]
    if given:
        yield given[0] + family[:2]
    yield family[:2] + family[-1]
    for letter in family[2:] + given:
        yield family[:2] + letter
    for n in range(2, 100):
        yield f"{family[:2]}{n}"


def _new_code(driver: dict, taken) -> str:
    own = driver.get("code", "")
    if own and own not in taken:
        return own
    return next(code for code in _code_candidates(driver) if code not in taken)


def _assign_codes(drivers: list[dict]) -> dict[str, str]:
    """driverId -> a code unique among these drivers (one season's), given
    in the order of who matters most to the season (most starts first)."""
    codes: dict[str, str] = {}
    # Drivers' own codes first, so a made-up one never takes a real one.
    for driver in drivers:
        own = driver.get("code", "")
        if own and own not in codes.values():
            codes[driver["driverId"]] = own
    # Then everyone's best candidate before anyone's second best, so a
    # one-off entrant's fallback can't take the code a regular would
    # naturally have: Scherrer, who raced once in 1953, can't be ASC while
    # Ascari ends up with something else.
    pending = {d["driverId"]: _code_candidates(d) for d in drivers if d["driverId"] not in codes}
    while pending:
        for driver_id, candidates in list(pending.items()):
            code = next(candidates)
            if code not in codes.values():
                codes[driver_id] = code
                del pending[driver_id]
    return codes


def _driver_code(season: int, driver: dict) -> str:
    """The driver's code in this season, as the season's race results set it."""
    with _season_codes_guard:
        known = season in _season_codes
    if not known:
        fetch_race_results(season)
    with _season_codes_guard:
        codes = _season_codes.setdefault(season, {})
        driver_id = driver.get("driverId", "")
        if driver_id not in codes:
            # Not in the race results: e.g. a qualifying entry who failed
            # to make the race.
            codes[driver_id] = _new_code(driver, set(codes.values()))
        return codes[driver_id]


# The per-race list key varies by endpoint; a race payload carries exactly one.
RESULT_KEYS = ("Results", "QualifyingResults", "SprintResults")


def paginate_races(path: str) -> list[dict]:
    """Every race in a paginated RaceTable response, e.g. for "2024/results"
    or "drivers/alonso/results/1"."""
    offset = 0
    all_races = []
    while True:
        url = f"{API_BASE_URL}/{path}.json?limit={PAGE_LIMIT}&offset={offset}"
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


def _paginate_races(endpoint: str, season: int) -> list[dict]:
    return paginate_races(f"{season}/{endpoint}")


@_shared_once_completed
def fetch_qualifying_results(season: int) -> pd.DataFrame:
    columns = [
        "season", "round", "race_name", "driver_id", "driver_code", "driver",
        "constructor", "qual_pos", "got_pole",
    ]
    if season < FIRST_CHAMPIONSHIP_SEASON:
        return pd.DataFrame(columns=columns)
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
                "driver_id": driver.get("driverId", ""),
                "driver_code": _driver_code(season, driver),
                "driver": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                "constructor": constructor.get("name", ""),
                "qual_pos": int(q["position"]),
                "got_pole": 1 if q["position"] == "1" else 0,
            })

    # Before the mid-1990s there is no qualifying data at all; the grades
    # use the grid in its place (see pipeline.py).
    return pd.DataFrame(rows, columns=columns)


# Entrants who never started. Until the 1990s the results list every
# entrant, so a 1980s race can carry half a dozen who failed to (pre-)qualify
# ("F"), and the 1950s list drivers who withdrew or never took the start
# ("W": Marimón at the 1954 German GP, killed in practice). Counted as starts,
# they would look like retirements and pass for race experience. From 2021 a
# "W" stays: a driver who missed the Grand Prix can still have raced that
# weekend's sprint (Sainz, Qatar 2023), whose points hang off the race row.
_DID_NOT_QUALIFY_STATUSES = {"Did not qualify", "Did not prequalify"}


def _started(season: int, res: dict) -> bool:
    pos_text = res.get("positionText", "")
    if pos_text == "F" or res.get("status", "") in _DID_NOT_QUALIFY_STATUSES:
        return False
    return pos_text != "W" or season >= FIRST_SPRINT_SEASON


def _one_row_per_driver_race(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse shared drives into one result per driver per race.

    Until 1957 drivers could hand their car to a teammate mid-race and share
    its points, and the same driver can appear twice in one race: their own
    car, and the one they took over. They raced once, so they get the better
    of the two results, with the points of both, from their own grid slot.
    """
    if df.empty or not df.duplicated(["round", "driver_id"]).any():
        return df.drop(columns="_order")
    df = df.copy()
    keys = ["round", "driver_id"]
    df["points_scored"] = df.groupby(keys)["points_scored"].transform("sum")
    df["got_win"] = df.groupby(keys)["got_win"].transform("max")
    # The car taken over has no grid slot for them (0, or none); their own
    # car's does.
    slots = df["grid_pos"].where(df["grid_pos"] > 0)
    df["grid_pos"] = slots.groupby([df["round"], df["driver_id"]]).transform("min").fillna(df["grid_pos"])
    return (
        df.sort_values(["round", "driver_id", "_order"])
        .drop_duplicates(keys)
        .sort_values(["round", "_order"])
        .drop(columns="_order")
        .reset_index(drop=True)
    )


_RACE_COLUMNS = [
    "season", "round", "race_name", "driver_id", "driver_code", "driver", "constructor",
    "grid_pos", "finish_pos", "position_text", "status", "laps", "time_millis", "points_scored",
    "got_win", "dnf", "retired",
]

# The statuses of a car that ran to the end. A classified car can still have
# retired: one that stops after 90% of the distance is classified, with the
# cause as its status (Vettel's alternator at Monza in 2012, classified 22nd).
FINISHED_STATUS = re.compile(r"Finished|Lapped|\+\d+ Laps?")


@_shared_once_completed
def fetch_race_results(season: int) -> pd.DataFrame:
    """Every starter's result in every round, one row per driver per race."""
    races = _paginate_races("results", season) if season >= FIRST_CHAMPIONSHIP_SEASON else []
    with _season_codes_guard:
        _season_entrants[season] = {
            (int(race["round"]), res["Driver"]["driverId"]) for race in races for res in race["Results"]
        }
    entries = [(race, res) for race in races for res in race["Results"] if _started(season, res)]
    starts: dict[str, set] = {}
    for race, res in entries:
        starts.setdefault(res["Driver"]["driverId"], set()).add(race["round"])
    drivers = {res["Driver"]["driverId"]: res["Driver"] for _, res in entries}
    codes = _assign_codes(sorted(drivers.values(), key=lambda d: (-len(starts[d["driverId"]]), d["driverId"])))
    with _season_codes_guard:
        _season_codes[season] = codes

    rows = []
    for race, res in entries:
        driver = res["Driver"]
        constructor = res["Constructor"]
        pos_text = res.get("positionText", "")

        is_classified = pos_text.lstrip("-").isdigit()
        # The classified position, not the classification order: two drivers
        # who shared the winning car (1951 France) are both classified P1.
        finish_pos = (int(pos_text) if pos_text.isdigit() else int(order)) if is_classified else None
        dnf = 0 if is_classified else 1
        # Total race time, given only to finishers on the lead lap.
        millis = (res.get("Time") or {}).get("millis")

        # Jolpica leaves out "points" when there are none recorded, and can
        # send a null grid or position for an old entry.
        grid = str(res.get("grid") or "")
        order = str(res.get("position") or "")
        laps = str(res.get("laps") or "")
        status = res.get("status") or ""

        rows.append({
            "season": season,
            "round": int(race["round"]),
            "race_name": race["raceName"],
            "driver_id": driver.get("driverId", ""),
            "driver_code": codes[driver["driverId"]],
            "driver": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
            "constructor": constructor.get("name", ""),
            # 0 is a pit-lane start, or in the early decades an unknown slot.
            "grid_pos": int(grid) if grid.isdigit() else None,
            "finish_pos": finish_pos,
            "position_text": pos_text,
            "status": status,
            # Laps completed; None when not recorded.
            "laps": int(laps) if laps.isdigit() else None,
            "time_millis": float(millis) if millis else None,
            "points_scored": float(res.get("points") or 0),
            "got_win": 1 if pos_text == "1" else 0,
            # Not classified: the official DNF.
            "dnf": dnf,
            # Didn't run to the end, classified or not.
            "retired": 0 if is_classified and FINISHED_STATUS.fullmatch(status) else 1,
            # The classification order, unclassified drivers included.
            "_order": int(order) if order.isdigit() else 10_000 + len(rows),
        })

    return _one_row_per_driver_race(pd.DataFrame(rows, columns=_RACE_COLUMNS + ["_order"]))


@_shared_once_completed
def fetch_sprint_points(season: int) -> pd.DataFrame:
    """Points each driver scored in each sprint. Race results leave these out."""
    rows = []
    races = _paginate_races("sprint", season) if season >= FIRST_SPRINT_SEASON else []
    for race in races:
        round_num = int(race["round"])
        for res in race["SprintResults"]:
            rows.append({
                "round": round_num,
                "driver_code": _driver_code(season, res["Driver"]),
                "sprint_points": float(res.get("points") or 0),
            })

    return pd.DataFrame(rows, columns=["round", "driver_code", "sprint_points"])


_DRIVER_STANDINGS_COLUMNS = [
    "Position", "Driver", "Driver Code", "Nationality", "Constructor", "Points", "Wins",
    # False for a driver the championship didn't place (see below), whose
    # "Position Text" then says why: "-" not classified, "D" disqualified,
    # "E" excluded.
    "Classified",
    "Position Text",
]


def _paginate_standings(path: str, key: str) -> list[dict]:
    """Every entry of a standings table. A 1950s championship lists more
    drivers than fit on one page (and the provider's default page is 30)."""
    offset = 0
    entries: list[dict] = []
    while True:
        url = f"{API_BASE_URL}/{path}.json?limit={PAGE_LIMIT}&offset={offset}"
        data = _get_json(url)
        try:
            total = int(data["MRData"]["total"])
            standings_list = data["MRData"]["StandingsTable"]["StandingsLists"]
            page = standings_list[0][key] if standings_list else []
        except (KeyError, ValueError) as exc:
            raise UpstreamAPIError(f"Unexpected response shape from {url}: {exc}") from exc
        entries.extend(page)
        offset += len(page)
        if not page or offset >= total:
            return entries


def _driver_standings(season: int, path: str) -> pd.DataFrame:
    standings = _paginate_standings(path, "DriverStandings")
    if not standings:
        return pd.DataFrame(columns=_DRIVER_STANDINGS_COLUMNS)

    rows = []
    unplaced = []
    for entry in standings:
        driver = entry["Driver"]
        constructor = entry["Constructors"][0] if entry.get("Constructors") else {}
        row = {
            "Position": None,
            "Driver": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
            "Driver Code": _driver_code(season, driver),
            "Nationality": driver.get("nationality", ""),
            "Constructor": constructor.get("name", ""),
            "Points": float(entry.get("points") or 0),
            "Wins": int(entry.get("wins") or 0),
            "Classified": True,
            "Position Text": str(entry.get("positionText") or entry.get("position") or "-"),
        }
        if str(entry.get("position") or "").isdigit():
            row["Position"] = int(entry["position"])
            row["Position Text"] = str(row["Position"])
            rows.append(row)
        else:
            unplaced.append(row)
    # Drivers without a championship position share the one after the last
    # classified driver: until 2001 only point scorers were classified (the
    # rest are "-"), and a driver disqualified from the championship
    # (Schumacher in 1997) has none either. Numbering them in the provider's
    # order would invent an order the championship never had.
    shared = (max(r["Position"] for r in rows) if rows else 0) + 1
    for row in sorted(unplaced, key=lambda r: -r["Points"]):
        row["Position"] = shared
        row["Classified"] = False
        if row["Position Text"] not in ("D", "E"):
            row["Position Text"] = "-"
        rows.append(row)

    return (
        pd.DataFrame(rows, columns=_DRIVER_STANDINGS_COLUMNS)
        .sort_values("Position", kind="stable")
        .reset_index(drop=True)
    )


@_shared_once_completed
def fetch_driver_standings(season: int) -> pd.DataFrame:
    if season < FIRST_CHAMPIONSHIP_SEASON:
        return pd.DataFrame(columns=_DRIVER_STANDINGS_COLUMNS)
    return _driver_standings(season, f"{season}/driverStandings")


def fetch_driver_standings_after(season: int, round_number: int) -> pd.DataFrame:
    """The drivers' championship as it stood after one round."""
    return _driver_standings(season, f"{season}/{round_number}/driverStandings")


@_shared_once_completed
def fetch_constructor_standings(season: int) -> pd.DataFrame:
    """The constructors' championship, which began in 1958: empty before it."""
    columns = ["Position", "Constructor", "Points", "Wins"]
    if season < FIRST_CONSTRUCTORS_SEASON:
        return pd.DataFrame(columns=columns)

    rows = []
    for entry in _paginate_standings(f"{season}/constructorStandings", "ConstructorStandings"):
        # An excluded constructor has no numeric position; it has no tier.
        if not str(entry.get("position") or "").isdigit():
            continue
        rows.append({
            "Position": int(entry["position"]),
            "Constructor": entry["Constructor"].get("name", ""),
            "Points": float(entry.get("points") or 0),
            "Wins": int(entry.get("wins") or 0),
        })

    return pd.DataFrame(rows, columns=columns).sort_values("Position").reset_index(drop=True)
