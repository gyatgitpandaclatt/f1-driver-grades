"""
Load a single race session (laps, weather, race control messages) via FastF1.
"""
from pathlib import Path

import fastf1
import fastf1.core
import pandas as pd

from ..config import FASTF1_CACHE_DIR

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / FASTF1_CACHE_DIR
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(_CACHE_DIR))


def load_race(year: int, round_number: int) -> fastf1.core.Session:
    session = fastf1.get_session(year, round_number, "R")
    session.load(telemetry=True, laps=True, weather=True, messages=True)
    return session


def get_laps(session: fastf1.core.Session) -> pd.DataFrame:
    # FastF1's laps frame already carries the driver abbreviation string in
    # `Driver` — no dict/lookup needed.
    return session.laps.copy()


def get_weather(session: fastf1.core.Session) -> pd.DataFrame:
    return session.weather_data


def get_race_control(session: fastf1.core.Session) -> pd.DataFrame:
    return session.race_control_messages
