"""
Find the moments that shaped a finished season.

For the title: championship lead changes, big points swings between the
leading drivers (a win against a rival's retirement), close finishes between
them, and where the title was decided. Beyond it: wins and first podiums for
drivers outside the championship's top five, rookies' first points, podiums
and wins, and points that were crucial to a midfield or backmarker team.
Part-time drivers are kept out of both and listed as footnotes.

Everything comes from race results, not lap data (see ingestion.py), so a
battle between contenders is two of them finishing next to each other a few
seconds apart: the closest honest proxy the data offers.

Every headline is built here from the data, not by the narrator, so the
tables on the page can be trusted even where the prose is loose.
"""
from itertools import combinations

import pandas as pd

from .. import career
from ..config import (
    SEASON_SUMMARY_CHAMPIONSHIP_DRIVERS,
    SEASON_SUMMARY_CLOSE_FINISH_SECONDS,
    SEASON_SUMMARY_CRUCIAL_POINTS_SHARE,
    SEASON_SUMMARY_MAX_OTHER_MOMENTS,
    SEASON_SUMMARY_MAX_TITLE_MOMENTS,
    SEASON_SUMMARY_MIDFIELD_FROM_POSITION,
    SEASON_SUMMARY_SWING_MIN_POINTS,
    SEASON_SUMMARY_TITLE_CONTENDERS,
)
from ..lineups import describe_rounds, driver_names, opening_lineups, stints
from .features import split_quarters

_UNCLASSIFIED = {"D": "DSQ", "E": "DSQ", "W": "DNS", "F": "DNQ"}


def _pts(value: float) -> str:
    """25.0 -> "25", 12.5 -> "12.5"."""
    return f"{value:g}"


def _points(value: float) -> str:
    return f"{_pts(value)} pt" if value == 1 else f"{_pts(value)} pts"


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def _result_text(row) -> str:
    """A driver's Grand Prix result: "P3", "DNF – Engine", "DSQ"."""
    if pd.notna(row.finish_pos):
        return f"P{int(row.finish_pos)}"
    label = _UNCLASSIFIED.get(row.position_text, "DNF")
    return f"{label} – {row.status}" if label == "DNF" and row.status else label


class SeasonData:
    """Lookups over one season's frames, shared by every detector below."""

    def __init__(self, season, race_df, weekend, table, driver_standings, constructor_standings, rookies, part_timers):
        self.season = season
        self.race_df = race_df
        self.weekend = weekend
        self.rookies = rookies
        self.part_timers = part_timers
        self.constructor_standings = constructor_standings
        self.rounds = sorted(int(r) for r in race_df["round"].unique())
        self.race_names = race_df.drop_duplicates("round").set_index("round")["race_name"].to_dict()
        self.names = driver_names(race_df)
        self.driver_ids = race_df.drop_duplicates("driver_code").set_index("driver_code")["driver_id"].to_dict()
        self.positions = table.pivot(index="round", columns="driver_code", values="position")
        self.points = table.pivot(index="round", columns="driver_code", values="points")
        self.round_points = weekend.pivot_table(
            index="round", columns="driver_code", values="points", aggfunc="sum"
        ).fillna(0.0)
        self.final_positions = driver_standings.set_index("Driver Code")["Position"].to_dict()
        self.championship_drivers = {
            code for code, pos in self.final_positions.items() if pos <= SEASON_SUMMARY_CHAMPIONSHIP_DRIVERS
        }
        self.results = {r: race_df[race_df["round"] == r].set_index("driver_code") for r in self.rounds}

    def leader(self, round_number: int) -> str:
        return self.positions.loc[round_number].idxmin()

    def driver_in_position(self, round_number: int, position: int) -> str | None:
        standings = self.positions.loc[round_number]
        match = standings[standings == position]
        return match.index[0] if len(match) else None

    def position_or_last(self, round_number: int, code: str) -> float:
        """Championship position after the round; a driver yet to race sorts last."""
        position = self.positions.at[round_number, code] if code in self.positions.columns else None
        return float(position) if pd.notna(position) else float("inf")

    def round_points_of(self, round_number: int, code: str) -> float:
        row = self.round_points.loc[round_number]
        return float(row[code]) if code in row.index else 0.0

    def finish_of(self, round_number: int, code: str) -> float | None:
        """Classified finishing position; None for a retirement or a missed race."""
        results = self.results[round_number]
        if code not in results.index or pd.isna(results.at[code, "finish_pos"]):
            return None
        return float(results.at[code, "finish_pos"])

    def result_of(self, round_number: int, code: str) -> str:
        results = self.results[round_number]
        return _result_text(results.loc[code]) if code in results.index else "did not race"

    def moment(self, round_number: int, kind: str, headline: str, drivers: list[str], importance: float) -> dict:
        return {
            "round": round_number,
            "race_name": self.race_names[round_number],
            "kinds": [kind],
            "headline": headline,
            "drivers": drivers,
            "importance": importance,
        }


def _merge_by_round(moments: list[dict], key) -> list[dict]:
    """One moment per key (e.g. per round), its headlines and kinds joined."""
    merged: dict = {}
    for m in moments:
        k = key(m)
        if k not in merged:
            merged[k] = dict(m, drivers=list(m["drivers"]))
            continue
        into = merged[k]
        into["kinds"] += [kind for kind in m["kinds"] if kind not in into["kinds"]]
        into["headline"] += f"; {m['headline']}"
        into["drivers"] += [d for d in m["drivers"] if d not in into["drivers"]]
        into["importance"] += m["importance"]
    return list(merged.values())


def _keep_most_important(moments: list[dict], limit: int) -> list[dict]:
    kept = sorted(moments, key=lambda m: -m["importance"])[:limit]
    return [
        {k: v for k, v in m.items() if k != "importance"}
        for m in sorted(kept, key=lambda m: m["round"])
    ]


def title_decided(s: SeasonData, sprint_rounds: set[int]) -> dict:
    """The first round after which nobody could catch the leader.

    "Could catch" assumes a rival wins every remaining Grand Prix and sprint
    with the most points anyone scored for one this season (so a fastest-lap
    bonus counts in the seasons that had one). A title still open at the
    finale is decided there.
    """
    max_race = float(s.weekend["points_scored"].max())
    max_sprint = float(s.weekend["sprint_points"].max())
    for i, round_number in enumerate(s.rounds):
        remaining = s.rounds[i + 1:]
        available = sum(max_race + (max_sprint if r in sprint_rounds else 0.0) for r in remaining)
        leader = s.leader(round_number)
        runner_up = s.driver_in_position(round_number, 2)
        lead = s.points.at[round_number, leader] - (s.points.at[round_number, runner_up] if runner_up else 0.0)
        if lead > available or not remaining:
            return {
                "round": round_number,
                "race_name": s.race_names[round_number],
                "driver_code": leader,
                "rounds_left": len(remaining),
            }
    raise AssertionError("unreachable: the final round always decides the title")


def title_moments(s: SeasonData, decided: dict) -> list[dict]:
    final_contenders = {
        code for code, pos in s.final_positions.items() if pos <= SEASON_SUMMARY_TITLE_CONTENDERS
    }
    moments = []
    for i, r in enumerate(s.rounds):
        previous = s.rounds[i - 1] if i else None
        # The top of the table going into this race. Round 1 has no table
        # yet, so it takes the drivers who ended the season there.
        contenders = (
            set(s.positions.loc[previous].nsmallest(SEASON_SUMMARY_TITLE_CONTENDERS).index)
            if previous is not None
            else final_contenders
        )
        contenders = sorted(contenders, key=lambda c: s.position_or_last(r, c))

        if decided["round"] == r:
            code = decided["driver_code"]
            when = (
                f"with {_plural(decided['rounds_left'], 'round')} to go"
                if decided["rounds_left"]
                else "at the final round"
            )
            moments.append(s.moment(r, "title_decided", f"{code} clinches the title {when}", [code], 10))

        if previous is not None and s.leader(r) != s.leader(previous):
            new, old = s.leader(r), s.leader(previous)
            runner_up = s.driver_in_position(r, 2)
            margin = s.points.at[r, new] - s.points.at[r, runner_up]
            moments.append(s.moment(
                r, "lead_change",
                f"{new} takes the championship lead from {old} (by {_points(margin)})",
                [new, old], 4,
            ))

        # A swing has to come from a win or a retirement; a big gap between
        # two ordinary finishes is just a weekend.
        swings = []
        for a, b in combinations(contenders, 2):
            delta = s.round_points_of(r, a) - s.round_points_of(r, b)
            if abs(delta) < SEASON_SUMMARY_SWING_MIN_POINTS:
                continue
            gainer, loser = (a, b) if delta > 0 else (b, a)
            if s.finish_of(r, gainer) == 1 or s.finish_of(r, loser) is None:
                swings.append((abs(delta), gainer, loser))
        if swings:
            swings.sort(key=lambda sw: -sw[0])
            involved = sorted({c for _, g, lo in swings for c in (g, lo)}, key=lambda c: s.position_or_last(r, c))
            gains = "; ".join(f"{g} gains {_points(n)} on {lo}" for n, g, lo in swings)
            results = ", ".join(f"{c} {s.result_of(r, c)}" for c in involved)
            moments.append(s.moment(r, "points_swing", f"{gains} ({results})", involved, swings[0][0] / 10))

        results = s.results[r]
        for a, b in combinations(contenders, 2):
            if a not in results.index or b not in results.index:
                continue
            ra, rb = results.loc[a], results.loc[b]
            if pd.isna(ra.finish_pos) or pd.isna(rb.finish_pos) or abs(ra.finish_pos - rb.finish_pos) != 1:
                continue
            if pd.isna(ra.time_millis) or pd.isna(rb.time_millis):
                continue
            gap = abs(ra.time_millis - rb.time_millis) / 1000
            if gap > SEASON_SUMMARY_CLOSE_FINISH_SECONDS:
                continue
            ahead, behind = (a, b) if ra.finish_pos < rb.finish_pos else (b, a)
            position = int(min(ra.finish_pos, rb.finish_pos))
            moments.append(s.moment(
                r, "contender_duel",
                f"{ahead} beats {behind} to P{position} by {gap:.1f}s",
                [ahead, behind], 3 if position == 1 else 2,
            ))

    merged = _merge_by_round(moments, key=lambda m: m["round"])
    return _keep_most_important(merged, SEASON_SUMMARY_MAX_TITLE_MOMENTS)


def _weekend_result(s: SeasonData, round_number: int, code: str) -> str:
    """"P8", "+2 in the sprint", or "P9, +1 in the sprint"."""
    row = s.weekend[(s.weekend["round"] == round_number) & (s.weekend["driver_code"] == code)].iloc[0]
    parts = []
    if row.points_scored > 0:
        parts.append(s.result_of(round_number, code))
    if row.sprint_points > 0:
        parts.append(f"+{_pts(row.sprint_points)} in the sprint")
    return ", ".join(parts)


def _first_finish_moments(s: SeasonData) -> list[dict]:
    """Wins and first podiums by drivers outside the championship's top
    five, and anyone's first win."""
    moments = []
    full_time = s.race_df[~s.race_df["driver_code"].isin(s.part_timers)]

    # Each driver's first win of the season is the only one that can be
    # their first ever, so the career is looked up once per winner.
    checked_first_win: set[str] = set()
    for row in full_time[full_time["finish_pos"] == 1].sort_values("round").itertuples():
        code, r = row.driver_code, int(row.round)
        first = False
        if code not in checked_first_win:
            checked_first_win.add(code)
            first = career.first_finish_at(row.driver_id, 1) == (s.season, r)
        outside = code not in s.championship_drivers
        if not (first or outside):
            continue
        headline = f"{code}'s first F1 win" if first else f"{code} wins"
        if code in s.rookies:
            headline += " as a rookie"
        if outside:
            headline += f" (P{s.final_positions.get(code, '?')} in the final standings)"
        moments.append(s.moment(r, "first_win" if first else "win_outside_top", headline, [code], 6 if first else 4))

    first_wins = {(m["round"], m["drivers"][0]) for m in moments if "first_win" in m["kinds"]}
    podiums = full_time[full_time["finish_pos"] <= 3].sort_values("round")
    for code, rows in podiums.groupby("driver_code"):
        if code in s.championship_drivers and code not in s.rookies:
            continue
        r = int(rows["round"].iloc[0])
        if (r, code) in first_wins or career.first_podium(s.driver_ids[code]) != (s.season, r):
            continue
        position = int(rows["finish_pos"].iloc[0])
        headline = f"{code}'s first F1 podium (P{position})"
        if code in s.rookies:
            headline += " as a rookie"
        moments.append(s.moment(r, "first_podium", headline, [code], 5))
    return moments


def _rookie_first_points(s: SeasonData) -> list[dict]:
    moments = []
    for code in sorted(s.rookies - s.part_timers):
        scored = s.weekend[(s.weekend["driver_code"] == code) & (s.weekend["points"] > 0)]
        if scored.empty:
            continue
        first_points = career.first_points_at(s.driver_ids[code])
        if first_points is not None and first_points < (s.season, 1):
            continue  # scored before, e.g. as a stand-in
        r = int(scored["round"].min())
        moments.append(s.moment(
            r, "rookie_first_points",
            f"{code} (rookie) scores first F1 points: {_weekend_result(s, r, code)}",
            [code], 4,
        ))
    return moments


def _crucial_team_points(s: SeasonData) -> list[dict]:
    """Weekends a midfield or backmarker team's season leaned on: a big share
    of its points total, or its first points after a pointless first quarter.

    Judged per team per weekend, not per driver, so a double podium counts
    as the one result it was. Part-time drivers' points are left out of it
    (they are footnoted). Whether the team could have kept its championship
    position without the points is said alongside, never on its own: when
    two teams finish three points apart, every score either made is
    "decisive", and listing them all says nothing the standings don't.
    """
    standings = s.constructor_standings.sort_values("Position").reset_index(drop=True)
    team_points = standings.set_index("Constructor")["Points"].to_dict()
    team_below = {
        row.Constructor: (standings.at[i + 1, "Constructor"], standings.at[i + 1, "Points"])
        for i, row in enumerate(standings.itertuples())
        if i + 1 < len(standings)
    }
    midfield = set(standings.loc[standings["Position"] >= SEASON_SUMMARY_MIDFIELD_FROM_POSITION, "Constructor"])
    team_first_round = s.weekend[s.weekend["points"] > 0].groupby("constructor")["round"].min().to_dict()
    first_quarter_end = split_quarters(s.rounds)[0][-1]

    scored = s.weekend[
        (s.weekend["points"] > 0)
        & s.weekend["constructor"].isin(midfield)
        & ~s.weekend["driver_code"].isin(s.part_timers)
    ]
    by_team: dict[str, list[dict]] = {}
    for (team, r), rows in scored.groupby(["constructor", "round"]):
        r = int(r)
        points = float(rows["points"].sum())
        total = team_points.get(team, 0.0)
        share = points / total if total > 0 else 0.0
        drought_over = team_first_round.get(team) == r and r > first_quarter_end
        if not (share >= SEASON_SUMMARY_CRUCIAL_POINTS_SHARE or drought_over):
            continue
        rival, rival_points = team_below.get(team, (None, None))
        decisive = rival is not None and total - points < rival_points
        reasons = []
        if drought_over:
            reasons.append(f"{team}'s first points of the season")
        if share >= SEASON_SUMMARY_CRUCIAL_POINTS_SHARE:
            reasons.append(f"{share:.0%} of {team}'s season total")
        if decisive:
            reasons.append(f"without them, {team} would have finished behind {rival}")
        drivers = list(rows.sort_values("points", ascending=False)["driver_code"])
        results = ", ".join(f"{code} {_weekend_result(s, r, code)}" for code in drivers)
        by_team.setdefault(team, []).append(s.moment(
            r, "crucial_points",
            f"{team} score {_points(points)} ({results}) — {'; '.join(reasons)}",
            drivers,
            2 + 4 * share + (2 if decisive else 0) + (1 if drought_over else 0),
        ))
    # A team with three points to its name makes each one a third of its
    # season; two of those say it.
    return [m for moments in by_team.values() for m in sorted(moments, key=lambda m: -m["importance"])[:2]]


def other_moments(s: SeasonData) -> list[dict]:
    moments = _first_finish_moments(s) + _rookie_first_points(s) + _crucial_team_points(s)
    merged = _merge_by_round(moments, key=lambda m: (m["round"], m["drivers"][0]))
    return _keep_most_important(merged, SEASON_SUMMARY_MAX_OTHER_MOMENTS)


def _career_firsts(s: SeasonData, code: str, rows: pd.DataFrame) -> list[str]:
    """A part-time driver's first F1 points, podium and win, where this season holds them."""
    driver_id = s.driver_ids[code]
    firsts = []
    checks = [("points", career.first_points_at, rows["points_scored"] > 0)]
    if (rows["finish_pos"] <= 3).any():
        checks.append(("podium", career.first_podium, rows["finish_pos"] <= 3))
    if (rows["finish_pos"] == 1).any():
        checks.append(("win", lambda d: career.first_finish_at(d, 1), rows["finish_pos"] == 1))
    for label, lookup, achieved in checks:
        if not achieved.any():
            continue
        first = lookup(driver_id)
        if first is not None and first[0] == s.season:
            r = first[1]
            firsts.append(f"first F1 {label} at the {s.race_names[r]} ({s.result_of(r, code)})")
    return firsts


def part_time_footnotes(s: SeasonData) -> list[dict]:
    """Every driver who raced too little to count as a full-season driver:
    whose seat they were in, what they scored, and any career firsts."""
    opening = opening_lineups(s.race_df)
    driven = stints(s.race_df)
    notes = []
    for code in sorted(s.part_timers, key=lambda c: (min(driven[k][0] for k in driven if k[0] == c), c)):
        rows = s.race_df[s.race_df["driver_code"] == code]
        car_stints = sorted(
            ({"constructor": team, "rounds": rounds} for (c, team), rounds in driven.items() if c == code),
            key=lambda st: st["rounds"][0],
        )
        in_place_of: list[str] = []
        for st in car_stints:
            team_rows = s.race_df[s.race_df["constructor"] == st["constructor"]]
            for r in st["rounds"]:
                in_car = set(team_rows.loc[team_rows["round"] == r, "driver_code"])
                for absent in opening.get(st["constructor"], []):
                    if absent not in in_car and absent not in in_place_of:
                        in_place_of.append(absent)
        points = float(s.weekend.loc[s.weekend["driver_code"] == code, "points"].sum())
        best = rows["finish_pos"].min()
        highlights = _career_firsts(s, code, rows)

        name = s.names.get(code, code)
        drove = "; ".join(f"{st['constructor']} in {describe_rounds(st['rounds'])}" for st in car_stints)
        summary = f"{name} ({code}): {_plural(len(rows), 'race')} — {drove}"
        if in_place_of:
            summary += f", in place of {', '.join(s.names.get(c, c) for c in in_place_of)}"
        summary += f". {_points(points)}" + (f", best finish P{int(best)}." if pd.notna(best) else ".")
        if highlights:
            summary += " " + "; ".join(h[0].upper() + h[1:] for h in highlights) + "."
        notes.append({
            "driver_code": code,
            "driver_name": name,
            "races": len(rows),
            "points": points,
            "best_finish": int(best) if pd.notna(best) else None,
            "stints": car_stints,
            "in_place_of": in_place_of,
            "highlights": highlights,
            "summary": summary,
        })
    return notes


def quarterly_breakdown(s: SeasonData) -> list[dict]:
    quarters = []
    before: int | None = None
    for number, rounds in enumerate(split_quarters(s.rounds), start=1):
        in_quarter = s.weekend[s.weekend["round"].isin(rounds)]
        scored = in_quarter.groupby("driver_code")["points"].sum().sort_values(ascending=False)
        winners = s.race_df[s.race_df["round"].isin(rounds) & (s.race_df["finish_pos"] == 1)]
        end = rounds[-1]
        leader = s.leader(end)
        runner_up = s.driver_in_position(end, 2)
        lead_changes = sum(
            1 for prev, r in zip([before] + rounds[:-1], rounds)
            if prev is not None and s.leader(r) != s.leader(prev)
        )
        quarters.append({
            "label": f"Q{number}",
            "first_round": rounds[0],
            "last_round": end,
            "first_race": s.race_names[rounds[0]],
            "last_race": s.race_names[end],
            "leader_at_start": s.leader(before) if before is not None else None,
            "leader": leader,
            "leader_points": float(s.points.at[end, leader]),
            "runner_up": runner_up,
            "margin": float(s.points.at[end, leader] - s.points.at[end, runner_up]) if runner_up else None,
            "lead_changes": lead_changes,
            "top_scorers": [{"driver_code": c, "points": float(p)} for c, p in scored.head(3).items()],
            "winners": [
                {"driver_code": c, "wins": int(n)} for c, n in winners["driver_code"].value_counts().items()
            ],
        })
        before = end
    return quarters
