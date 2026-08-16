"""
detect notable events in race and label them
"""
import pandas as pd


def detect_overtakes(position_matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Detect overtakes by comparing the position of each driver on consecutive laps. An overtake is detected when a driver moves up in position from one lap to the next.
    """
    overtakes = []
    for lap in range(2, len(position_matrix)):
        prev = position_matrix.loc[lap - 1]
        current = position_matrix.loc[lap]
        for d1 in position_matrix.columns:
            for d2 in position_matrix.columns:
                if d1 == d2:
                    continue
                if prev[d1] > prev[d2] and current[d1] < current[d2]:
                    overtakes.append({
                        'Lap': lap,
                        'OvertakingDriver': d1,
                        'OvertakenDriver': d2,
                    })
    return pd.DataFrame(overtakes)


def _longest_consecutive_close_run(common_laps: list[int], gap: pd.Series, threshold: pd.Timedelta) -> int:
    best = current = 0
    prev_lap = None
    for lap in common_laps:
        adjacent = prev_lap is not None and lap == prev_lap + 1
        close = bool(gap.loc[lap] < threshold)
        current = current + 1 if (adjacent and close) else (1 if close else 0)
        best = max(best, current)
        prev_lap = lap
    return best


def find_battles(laps_df: pd.DataFrame, gap_threshold: float = 1.0, min_laps: int = 3) -> list[dict]:
    """
    Detect close on-track battles: pairs of drivers whose lap times stayed
    within `gap_threshold` seconds of each other for at least `min_laps`
    *consecutive* laps — a sustained fight, not scattered coincidental gaps
    (e.g. two midfield cars quietly running similar one-off lap times on
    opposite sides of a pit stop, laps apart, isn't a "battle").
    """
    threshold = pd.Timedelta(seconds=gap_threshold)
    drivers = laps_df['Driver'].unique()
    lap_times_by_driver = {
        d: laps_df[laps_df['Driver'] == d].set_index('LapNumber')['LapTime']
        for d in drivers
    }

    battles = []
    for driver1 in drivers:
        for driver2 in drivers:
            if driver1 >= driver2:
                continue
            t1 = lap_times_by_driver[driver1]
            t2 = lap_times_by_driver[driver2]
            common_laps = sorted(t1.index.intersection(t2.index))
            if not common_laps:
                continue
            gap = (t1.loc[common_laps] - t2.loc[common_laps]).abs()
            longest_run = _longest_consecutive_close_run(common_laps, gap, threshold)
            if longest_run >= min_laps:
                battles.append({'Driver1': driver1, 'Driver2': driver2, 'CloseLaps': longest_run})
    return battles
