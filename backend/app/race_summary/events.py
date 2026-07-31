"""
detect notable events in race and label them
"""
import pandas as pd


def detect_overtakes(position_matrix: pd.DataFrame, track_status_by_lap: dict[int, str] | None = None) -> pd.DataFrame:
    """
    Detect overtakes by comparing the position of each driver on consecutive laps. An overtake is detected when a driver moves up in position from one lap to the next.
    """
    track_status_by_lap = track_status_by_lap or {}
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
                        'TrackStatus': track_status_by_lap.get(lap, 'GREEN'),
                    })
    return pd.DataFrame(overtakes)


def build_track_status_by_lap(rc_messages: pd.DataFrame, total_laps: int) -> dict[int, str]:
    """
    Forward-filled per-lap track status ('GREEN', 'SC', 'VSC') derived from
    race control message text and the lap number each message was logged on.
    """
    if 'Lap' not in rc_messages.columns or 'Message' not in rc_messages.columns:
        return {lap: 'GREEN' for lap in range(1, total_laps + 1)}

    transitions: dict[int, str] = {}
    for _, row in rc_messages.sort_values('Time').iterrows():
        lap = row.get('Lap')
        if pd.isna(lap):
            continue
        lap = int(lap)
        message = str(row.get('Message', '')).upper()
        if 'VIRTUAL SAFETY CAR DEPLOYED' in message:
            transitions[lap] = 'VSC'
        elif 'VIRTUAL SAFETY CAR ENDING' in message:
            transitions[lap] = 'GREEN'
        elif 'SAFETY CAR DEPLOYED' in message:
            transitions[lap] = 'SC'
        elif 'SAFETY CAR IN THIS LAP' in message or 'SAFETY CAR ENDING' in message:
            transitions[lap] = 'GREEN'

    status_by_lap: dict[int, str] = {}
    current = 'GREEN'
    for lap in range(1, total_laps + 1):
        if lap in transitions:
            current = transitions[lap]
        status_by_lap[lap] = current
    return status_by_lap


def detect_safety_cars(rc_messages: pd.DataFrame) -> list[dict]:
    sc_events = rc_messages[rc_messages['Message'].str.contains('Safety Car', case=False, na=False)]
    columns = [c for c in ('Time', 'Message', 'Lap') if c in sc_events.columns]
    return sc_events[columns].to_dict('records')


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


def driver_telemetry_sum(session, driver_code: str) -> dict:
    driver_laps = session.laps.pick_drivers(driver_code)

    max_speed = float('-inf')
    top_speed_lap = None
    speed_chunks = []
    rpm_chunks = []
    total_distance = 0.0

    for _, lap in driver_laps.iterlaps():
        tel = lap.get_car_data().add_distance()
        if tel.empty:
            continue

        speed_chunks.append(tel['Speed'])
        rpm_chunks.append(tel['RPM'])
        total_distance += tel['Distance'].max()

        lap_max_speed = tel['Speed'].max()
        if lap_max_speed > max_speed:
            max_speed = lap_max_speed
            top_speed_lap = lap['LapNumber']

    all_speeds = pd.concat(speed_chunks) if speed_chunks else pd.Series(dtype=float)
    all_rpms = pd.concat(rpm_chunks) if rpm_chunks else pd.Series(dtype=float)

    return {
        'MaxSpeed': all_speeds.max() if not all_speeds.empty else None,
        'AvgSpeed': all_speeds.mean() if not all_speeds.empty else None,
        'MaxRPM': all_rpms.max() if not all_rpms.empty else None,
        'AvgRPM': all_rpms.mean() if not all_rpms.empty else None,
        'top_speed_lap': top_speed_lap,
        'TotalDistance': total_distance,
    }
