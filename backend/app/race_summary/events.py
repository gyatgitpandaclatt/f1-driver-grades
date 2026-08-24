"""
detect notable events in race and label them
"""
import pandas as pd


def detect_overtakes(
    position_matrix: pd.DataFrame, pit_laps_by_driver: dict[str, set[int]] | None = None
) -> pd.DataFrame:
    """
    Detect on-track overtakes: a driver who was behind another on one lap and
    ahead of them on the next.

    Position changes caused by a pit stop are excluded. When a driver pits,
    everyone behind gains a place and gets it back when they rejoin, which is
    a swap in the classification but nothing that happened on track — a report
    built from those describes drivers passing cars that were in the pit lane.
    A swap is dropped when either driver pitted on that lap or the one before
    (Ergast records the lap a driver entered the pits, and the change surfaces
    on that lap or the next).

    This trades a few genuine passes that coincide with someone's stop for not
    inventing passes that never happened, which is the right way round for a
    report presented as fact.
    """
    pit_laps_by_driver = pit_laps_by_driver or {}

    def pitted_around(driver: str, lap: int) -> bool:
        laps = pit_laps_by_driver.get(driver, ())
        return lap in laps or (lap - 1) in laps

    overtakes = []
    # Walk the index itself rather than range(2, len(matrix)): lap numbers are
    # labels, not row offsets. Treating them as offsets crashed on any gap in
    # the lap data, and silently dropped the final lap even without one.
    laps = list(position_matrix.index)
    for prev_lap, lap in zip(laps, laps[1:]):
        prev = position_matrix.loc[prev_lap]
        current = position_matrix.loc[lap]
        for d1 in position_matrix.columns:
            for d2 in position_matrix.columns:
                if d1 == d2:
                    continue
                if prev[d1] > prev[d2] and current[d1] < current[d2]:
                    if pitted_around(d1, lap) or pitted_around(d2, lap):
                        continue
                    overtakes.append({
                        'Lap': lap,
                        'OvertakingDriver': d1,
                        'OvertakenDriver': d2,
                    })
    return pd.DataFrame(overtakes)


def _longest_consecutive_close_run(common_laps: list[int], is_close) -> int:
    """Longest run of consecutive laps for which `is_close(lap)` holds."""
    best = current = 0
    prev_lap = None
    for lap in common_laps:
        consecutive = prev_lap is not None and lap == prev_lap + 1
        close = is_close(lap)
        current = current + 1 if (consecutive and close) else (1 if close else 0)
        best = max(best, current)
        prev_lap = lap
    return best


def _positions_adjacent(position_matrix: pd.DataFrame, lap: int, d1: str, d2: str) -> bool:
    """Whether the two drivers held neighbouring positions on this lap."""
    if lap not in position_matrix.index:
        return False
    for driver in (d1, d2):
        if driver not in position_matrix.columns:
            return False
    p1 = position_matrix.at[lap, d1]
    p2 = position_matrix.at[lap, d2]
    if pd.isna(p1) or pd.isna(p2):
        return False
    return abs(float(p1) - float(p2)) == 1


def find_battles(
    laps_df: pd.DataFrame,
    position_matrix: pd.DataFrame,
    gap_threshold: float = 1.0,
    min_laps: int = 3,
) -> list[dict]:
    """
    Detect sustained on-track battles: pairs of drivers who held *neighbouring
    positions* while lapping within `gap_threshold` seconds of each other, for
    at least `min_laps` consecutive laps.

    Position adjacency is the load-bearing half. Lap-time similarity alone says
    nothing about whether two cars are racing: in a modern field almost every
    pair laps within a second of almost every other pair, so on that test alone
    a whole grid strung out over a minute of track reads as one giant battle,
    and the report presents cars that never saw each other as a fight.

    Ergast gives no gap-to-car-ahead, so "neighbouring positions plus matched
    pace" is the closest honest proxy available here. It still cannot tell a
    close scrap from two evenly matched cars running four seconds apart in
    P8 and P9 — it only guarantees they were adjacent in the order.
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

            def is_close(lap: int, gap=gap, d1=driver1, d2=driver2) -> bool:
                return bool(gap.loc[lap] < threshold) and _positions_adjacent(
                    position_matrix, lap, d1, d2
                )

            longest_run = _longest_consecutive_close_run(common_laps, is_close)
            if longest_run >= min_laps:
                battles.append({'Driver1': driver1, 'Driver2': driver2, 'CloseLaps': longest_run})
    return battles
