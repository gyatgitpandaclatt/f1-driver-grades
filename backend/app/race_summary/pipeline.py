"""
Orchestrate the race summarizer: FastF1 ingestion -> event/feature extraction ->
Claude narrative -> a single JSON-serializable dict matching RaceSummaryResponse.
"""
from datetime import datetime, timezone

import pandas as pd

from ..config import SEASON
from ..data_fetch import fetch_race_results
from ..exceptions import RaceSessionNotAvailableError
from . import events, features, narrator
from .ingestion import get_laps, get_race_control, get_weather, load_race


def _latest_completed_round(season: int) -> int:
    race_df = fetch_race_results(season)
    if race_df.empty:
        raise RaceSessionNotAvailableError(f"No completed races found for the {season} season yet.")
    return int(race_df['round'].max())


def _weather_summary(weather_df: pd.DataFrame) -> str:
    if weather_df.empty:
        return "No weather data available."
    conditions = "wet" if weather_df['Rainfall'].any() else "dry"
    avg_temp = weather_df['AirTemp'].mean()
    return f"Conditions were {conditions} with an average air temperature of {avg_temp:.1f}°C."


def run_race_summary_pipeline(season: int = SEASON) -> dict:
    round_number = _latest_completed_round(season)

    try:
        session = load_race(season, round_number)
    except Exception as exc:
        raise RaceSessionNotAvailableError(
            f"FastF1 has no session data yet for {season} round {round_number}: {exc}"
        ) from exc

    laps_df = get_laps(session)
    weather_df = get_weather(session)
    rc_messages = get_race_control(session)

    total_laps = int(laps_df['LapNumber'].max())

    # official classification (not reconstructed from laps, which has one row
    # per driver per lap and no notion of "final order")
    results_df = session.results.dropna(subset=['Position']).sort_values('Position')
    final_classification = [
        {'position': int(row['Position']), 'driver_code': row['Abbreviation']}
        for _, row in results_df.iterrows()
    ]
    top_drivers = results_df['Abbreviation'].head(3).tolist()

    # feature extraction
    pit_stops_df = features.extract_pit_stops(laps_df)
    position_matrix = features.build_position_matrix(laps_df)
    strategies = features.summarize_strategy(laps_df)

    # event detection
    track_status_by_lap = events.build_track_status_by_lap(rc_messages, total_laps)
    overtakes_df = events.detect_overtakes(position_matrix, track_status_by_lap)
    safety_cars = events.detect_safety_cars(rc_messages)
    battles = events.find_battles(laps_df)

    # telemetry — top 3 finishers only, for the speed trace chart + narrative highlight
    telemetry_highlights = []
    speed_traces: dict[str, list[dict]] = {}
    for driver in top_drivers:
        summary = events.driver_telemetry_sum(session, driver)
        telemetry_highlights.append({
            'driver': driver,
            'max_speed_kph': float(summary['MaxSpeed']) if summary['MaxSpeed'] is not None else None,
            'top_speed_lap': int(summary['top_speed_lap']) if summary['top_speed_lap'] is not None else None,
        })

        fastest_lap = session.laps.pick_drivers(driver).pick_fastest()
        tel = fastest_lap.get_car_data().add_distance()
        speed_traces[driver] = [
            {'distance': float(dist), 'speed': float(speed)}
            for dist, speed in zip(tel['Distance'], tel['Speed'])
        ]

    context = {
        'race_name': session.event['EventName'],
        'year': int(season),
        'round': round_number,
        'total_laps': total_laps,
        'weather_summary': _weather_summary(weather_df),
        'final_classification': final_classification,
        'pit_stops': [
            {
                'driver': row['Driver'],
                'lap_number': int(row['LapNumber']),
                'compound': row['Compound'],
                'duration_seconds': row['PitStopDuration'],
                'tyre_life': row['TyreLife'],
            }
            for _, row in pit_stops_df.iterrows()
        ],
        'overtakes': [
            {
                'lap': int(row['Lap']),
                'overtaking_driver': row['OvertakingDriver'],
                'overtaken_driver': row['OvertakenDriver'],
                'track_status': row['TrackStatus'],
            }
            for _, row in overtakes_df.iterrows()
        ],
        'key_events': [
            {
                'time': str(m.get('Time')),
                'message': m.get('Message'),
                'lap': int(m['Lap']) if m.get('Lap') is not None and not pd.isna(m.get('Lap')) else None,
            }
            for m in safety_cars
        ],
        'strategies': [
            {'driver': driver, 'compound': s['Compound'], 'lap_start': s['LapStart'], 'lap_end': s['LapEnd']}
            for driver, stints in strategies.items()
            for s in stints
        ],
        'battles': [
            {'driver1': b['Driver1'], 'driver2': b['Driver2'], 'close_laps': b['CloseLaps']}
            for b in battles
        ],
        'telemetry_highlights': telemetry_highlights,
    }

    sections = narrator.generate_narrative(context)

    position_series = []
    for lap, row in position_matrix.iterrows():
        entry: dict = {'lap': int(lap)}
        for driver in position_matrix.columns:
            value = row[driver]
            if pd.notna(value):
                entry[driver] = float(value)
        position_series.append(entry)

    return {
        'status': 'ok',
        'season': int(season),
        'round': round_number,
        'race_name': context['race_name'],
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'sections': sections,
        'context': context,
        'charts': {
            'position_series': position_series,
            'speed_traces': speed_traces,
        },
    }
