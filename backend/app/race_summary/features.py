"""
Turn Ergast's raw laps/pit-stop records into the position matrix and lap-time
table the rest of race_summary works from.
"""
import pandas as pd


def _parse_ergast_time(time_str: str) -> pd.Timedelta:
    """Ergast times are "M:SS.sss" or, for sub-minute durations, "SS.sss"."""
    if ":" in time_str:
        minutes, rest = time_str.split(":", 1)
        return pd.Timedelta(minutes=int(minutes)) + pd.Timedelta(seconds=float(rest))
    return pd.Timedelta(seconds=float(time_str))


def build_position_matrix(laps: list[dict], driver_id_to_code: dict[str, str]) -> pd.DataFrame:
    """
    Rows are lap numbers, columns are driver codes, values are that driver's
    position on that lap. Unlike the FastF1 version, Ergast gives position
    directly per lap -- no need to derive it from timing data.
    """
    rows: dict[int, dict[str, int]] = {}
    for lap in laps:
        lap_number = int(lap["number"])
        row = rows.setdefault(lap_number, {})
        for timing in lap["Timings"]:
            code = driver_id_to_code.get(timing["driverId"], timing["driverId"])
            row[code] = int(timing["position"])
    return pd.DataFrame.from_dict(rows, orient="index").sort_index()


def build_lap_times(laps: list[dict], driver_id_to_code: dict[str, str]) -> pd.DataFrame:
    """Long-format Driver/LapNumber/LapTime table, for events.find_battles."""
    rows = []
    for lap in laps:
        lap_number = int(lap["number"])
        for timing in lap["Timings"]:
            code = driver_id_to_code.get(timing["driverId"], timing["driverId"])
            rows.append({
                "Driver": code,
                "LapNumber": lap_number,
                "LapTime": _parse_ergast_time(timing["time"]),
            })
    # One row per driver per lap. A repeated timing row (an overlapping page
    # from the provider) would otherwise give a driver a duplicated index and
    # make the pairwise gap computation in find_battles raise.
    return pd.DataFrame(rows).drop_duplicates(subset=["Driver", "LapNumber"], keep="first")


def extract_pit_stops(pit_stops: list[dict], driver_id_to_code: dict[str, str]) -> pd.DataFrame:
    """
    No tire compound data is available from Ergast (FastF1-only) -- this is
    lap number and duration only.
    """
    rows = []
    for stop in pit_stops:
        code = driver_id_to_code.get(stop["driverId"], stop["driverId"])
        rows.append({
            "Driver": code,
            "LapNumber": int(stop["lap"]),
            "StopNumber": int(stop["stop"]),
            "PitStopDuration": _parse_ergast_time(stop["duration"]).total_seconds(),
        })
    return pd.DataFrame(rows)
