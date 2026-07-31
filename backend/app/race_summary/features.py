"""
extracting features from the laps data: pit stops, position history, and tire strategy.
"""
import pandas as pd


def extract_pit_stops(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract pit stop information per driver: pair each in-lap (PitInTime set)
    with the following out-lap (PitOutTime set) to compute stop duration and
    the compound fitted during that stop.
    """
    pit_stops = []
    for driver, group in laps_df.sort_values('LapNumber').groupby('Driver'):
        group = group.reset_index(drop=True)
        in_lap_positions = group.index[group['PitInTime'].notna()]
        for pos in in_lap_positions:
            in_row = group.loc[pos]
            out_candidates = group.loc[pos + 1:]
            out_matches = out_candidates[out_candidates['PitOutTime'].notna()]
            if out_matches.empty:
                continue
            out_row = out_matches.iloc[0]
            duration = (out_row['PitOutTime'] - in_row['PitInTime']).total_seconds()
            pit_stops.append({
                'Driver': driver,
                'LapNumber': int(in_row['LapNumber']),
                'Compound': out_row.get('Compound'),
                'PitStopDuration': duration,
                'TyreLife': out_row.get('TyreLife'),
            })
    return pd.DataFrame(pit_stops)


def build_position_matrix(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    return a pivot table where the rows are the lap numbers, the columns are the drivers, and the values are the positions of each driver on each lap.
    """
    return laps_df.pivot_table(index='LapNumber', columns='Driver', values='Position')


def summarize_strategy(laps_df: pd.DataFrame) -> dict[str, list[dict]]:
    """
    per-driver tire stint summary: compound, lap start, and lap end
    """
    stints: dict[str, list[dict]] = {}
    for driver, group in laps_df.sort_values('LapNumber').groupby('Driver'):
        group = group.copy()
        group['Compound'] = group['Compound'].fillna('UNKNOWN')

        driver_stints = []
        previous_compound = None
        stint_start = int(group['LapNumber'].iloc[0])
        for _, row in group.iterrows():
            if row['Compound'] != previous_compound and previous_compound is not None:
                driver_stints.append({
                    'Compound': previous_compound,
                    'LapStart': stint_start,
                    'LapEnd': int(row['LapNumber']) - 1,
                })
                stint_start = int(row['LapNumber'])
            previous_compound = row['Compound']

        driver_stints.append({
            'Compound': previous_compound,
            'LapStart': stint_start,
            'LapEnd': int(group['LapNumber'].max()),
        })
        stints[driver] = driver_stints
    return stints
