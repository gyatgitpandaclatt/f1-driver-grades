import requests
import pandas as pd

from .config import API_BASE_URL, PAGE_LIMIT, REQUEST_TIMEOUT
from .exceptions import UpstreamAPIError


def _get_json(url: str) -> dict:
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except (requests.RequestException, ValueError) as exc:
        raise UpstreamAPIError(f"Failed to fetch {url}: {exc}") from exc


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

        offset += PAGE_LIMIT
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
