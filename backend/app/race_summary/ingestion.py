"""
Fetch a single race's results, lap times, and pit stops from the Jolpica/Ergast
API (the same provider the rest of this app already uses). Unlike FastF1, this
has no telemetry, tire compound, weather, or race-control data -- see
race_summary/README notes in pipeline.py for what that means for the narrative.
"""
from ..config import API_BASE_URL, PAGE_LIMIT
from ..data_fetch import _get_json
from ..exceptions import RaceSessionNotAvailableError, UpstreamAPIError


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

        if not races:
            break
        for lap in races[0]["Laps"]:
            lap_number = int(lap["number"])
            laps_by_number.setdefault(lap_number, []).extend(lap["Timings"])

        offset += PAGE_LIMIT
        if offset >= total:
            break

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
        all_stops.extend(races[0]["PitStops"])

        offset += PAGE_LIMIT
        if offset >= total:
            break

    return all_stops
