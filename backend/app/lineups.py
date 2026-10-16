"""
Lineup changes, read from who actually drove for whom.

The results feed records which car every driver drove in every round, so a
stand-in, a swap between teams, or a mid-season replacement all show up as
a constructor's lineup changing from one round to the next. What the feed
never says is why; config.LINEUP_CHANGE_REASONS supplies that where someone
has written it down.

Input everywhere is a season's race results as returned by
data_fetch.fetch_race_results (one row per driver per round).
"""
import pandas as pd

from .config import LINEUP_CHANGE_REASONS


def driver_names(race_df: pd.DataFrame) -> dict[str, str]:
    return race_df.drop_duplicates("driver_code").set_index("driver_code")["driver"].to_dict()


def opening_lineups(race_df: pd.DataFrame) -> dict[str, list[str]]:
    """Each constructor's drivers in the first round it raced this season."""
    lineups = {}
    for constructor, team in race_df.groupby("constructor"):
        first = team["round"].min()
        lineups[constructor] = sorted(team.loc[team["round"] == first, "driver_code"])
    return lineups


def stints(race_df: pd.DataFrame) -> dict[tuple[str, str], list[int]]:
    """(driver code, constructor) -> the rounds that driver drove that car."""
    return {
        (code, constructor): sorted(int(r) for r in rows["round"].unique())
        for (code, constructor), rows in race_df.groupby(["driver_code", "constructor"])
    }


def describe_rounds(rounds: list[int]) -> str:
    """[3, 4, 5, 9] -> "rounds 3–5 and 9"; [7] -> "round 7"."""
    spans: list[str] = []
    start = prev = None
    for r in sorted(rounds):
        if start is None:
            start = prev = r
        elif r == prev + 1:
            prev = r
        else:
            spans.append(f"{start}–{prev}" if prev != start else str(start))
            start = prev = r
    if start is not None:
        spans.append(f"{start}–{prev}" if prev != start else str(start))
    if len(spans) == 1 and "–" not in spans[0]:
        return f"round {spans[0]}"
    listed = spans[0] if len(spans) == 1 else ", ".join(spans[:-1]) + f" and {spans[-1]}"
    return f"rounds {listed}"


def _join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + f" and {names[-1]}"


def lineup_changes(race_df: pd.DataFrame) -> list[dict]:
    """Every round where a constructor's lineup differed from its previous
    round: who came in and whose seat they took."""
    changes = []
    for constructor, team in race_df.groupby("constructor"):
        previous: set[str] | None = None
        for round_number, rows in team.groupby("round"):
            current = set(rows["driver_code"])
            # A seat left empty with nobody new in it (a driver who failed
            # to qualify, or a team running one car for a race) isn't a
            # change: the lineup is the same when the driver is back.
            if previous is not None and current < previous:
                continue
            if previous is not None and current != previous:
                incoming = sorted(current - previous)
                outgoing = sorted(previous - current)
                for i in range(max(len(incoming), len(outgoing))):
                    changes.append({
                        "round": int(round_number),
                        "race_name": rows["race_name"].iloc[0],
                        "constructor": constructor,
                        "driver_in": incoming[i] if i < len(incoming) else None,
                        "driver_out": outgoing[i] if i < len(outgoing) else None,
                    })
            previous = current
    return sorted(changes, key=lambda c: (c["round"], c["constructor"]))


def change_reason(season: int, driver_code: str, constructor: str) -> str | None:
    for entry in LINEUP_CHANGE_REASONS:
        if (entry["season"], entry["driver_code"], entry["constructor"]) == (season, driver_code, constructor):
            return entry["reason"]
    return None


def race_lineup_notes(race_df: pd.DataFrame, season: int, round_number: int) -> list[str]:
    """Plain-fact notes for one race about every driver not in the seat their
    team started the season with.

    Gated on everyone who *started* the race, not the classification: a
    stand-in who retired is exactly the driver a report most needs to
    explain. Nothing is said about why, unless a reason is configured.
    """
    names = driver_names(race_df)
    opening = opening_lineups(race_df)
    driven = stints(race_df)
    this_race = race_df[race_df["round"] == round_number]
    team_in_race = this_race.set_index("driver_code")["constructor"].to_dict()

    notes = []
    for constructor, team in this_race.groupby("constructor"):
        lineup = set(team["driver_code"])
        started_with = opening.get(constructor, [])
        for code in sorted(lineup):
            reason = change_reason(season, code, constructor)
            if code in started_with:
                # Already in the seat at the start of the season; only a
                # configured reason has anything to add.
                if reason:
                    notes.append(f"{names.get(code, code)} drove for {constructor} in this race. {reason}")
                continue
            name = names.get(code, code)
            parts = [
                f"{name} drove for {constructor} in this race.",
                f"{constructor} started the season with "
                f"{_join_names([names.get(c, c) for c in started_with])}; "
                f"{name} has driven for the team in "
                f"{describe_rounds(driven[(code, constructor)])} of the {round_number} run so far.",
            ]
            for absent in sorted(set(started_with) - lineup):
                elsewhere = team_in_race.get(absent)
                parts.append(
                    f"{names.get(absent, absent)} drove for {elsewhere} in this race."
                    if elsewhere
                    else f"{names.get(absent, absent)} did not take part in this race."
                )
            if reason:
                parts.append(reason)
            notes.append(" ".join(parts))
    return notes
