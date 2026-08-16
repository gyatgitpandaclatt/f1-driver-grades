"""
Orchestrate the race summarizer: Jolpica/Ergast ingestion -> event/feature
extraction -> Claude narrative -> a single JSON-serializable dict matching
RaceSummaryResponse.

Ergast has no telemetry, tire compound, weather, or race-control data (that
was FastF1-only, and FastF1's data source blocks Replit's IP ranges — see
git history). This pipeline is deliberately a smaller feature set than that
version: final classification, pit stop timing (no compound), overtakes, and
close-battle detection, all derivable from Ergast's results/laps/pitstops
endpoints — the same provider the rest of this app already uses successfully
on Replit.
"""
from datetime import datetime, timezone

import pandas as pd

from ..config import SEASON
from ..data_fetch import fetch_race_results
from ..exceptions import RaceSessionNotAvailableError
from . import events, features, ingestion, narrator


def _latest_completed_round(season: int) -> int:
    race_df = fetch_race_results(season)
    if race_df.empty:
        raise RaceSessionNotAvailableError(f"No completed races found for the {season} season yet.")
    return int(race_df['round'].max())


def run_race_summary_pipeline(season: int = SEASON) -> dict:
    round_number = _latest_completed_round(season)

    event = ingestion.fetch_race_event(season, round_number)
    race_name = event['raceName']
    results = event['Results']

    driver_id_to_code = {
        r['Driver']['driverId']: r['Driver'].get('code') or r['Driver']['driverId'][:3].upper()
        for r in results
    }

    final_classification = []
    for r in results:
        pos_text = r.get('positionText', '')
        if not pos_text.lstrip('-').isdigit():
            continue
        final_classification.append({
            'position': int(r['position']),
            'driver_code': driver_id_to_code[r['Driver']['driverId']],
            'status': r['status'],
        })
    final_classification.sort(key=lambda entry: entry['position'])

    laps = ingestion.fetch_laps(season, round_number)
    pit_stops_raw = ingestion.fetch_pit_stops(season, round_number)
    total_laps = max((int(lap['number']) for lap in laps), default=0)

    position_matrix = features.build_position_matrix(laps, driver_id_to_code)
    lap_times_df = features.build_lap_times(laps, driver_id_to_code)
    pit_stops_df = features.extract_pit_stops(pit_stops_raw, driver_id_to_code)

    overtakes_df = events.detect_overtakes(position_matrix)
    battles = events.find_battles(lap_times_df)

    context = {
        'race_name': race_name,
        'year': int(season),
        'round': round_number,
        'total_laps': total_laps,
        'final_classification': final_classification,
        'pit_stops': [
            {
                'driver': row['Driver'],
                'lap_number': int(row['LapNumber']),
                'stop_number': int(row['StopNumber']),
                'duration_seconds': row['PitStopDuration'],
            }
            for _, row in pit_stops_df.iterrows()
        ],
        'overtakes': [
            {
                'lap': int(row['Lap']),
                'overtaking_driver': row['OvertakingDriver'],
                'overtaken_driver': row['OvertakenDriver'],
            }
            for _, row in overtakes_df.iterrows()
        ],
        'battles': [
            {'driver1': b['Driver1'], 'driver2': b['Driver2'], 'close_laps': b['CloseLaps']}
            for b in battles
        ],
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
        'race_name': race_name,
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'sections': sections,
        'context': context,
        'charts': {
            'position_series': position_series,
        },
    }
