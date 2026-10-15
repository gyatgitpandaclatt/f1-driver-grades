"""
Convert a finished season's structured championship data into a season
review via an LLM (Gemini first, Cerebras as the fallback — see
narrator_base).
"""
from ..narrator_base import compact, generate_report, section_guide

SYSTEM_PROMPT = """You are a professional Formula 1 journalist writing an end-of-season
review in the style of Autosport or The Race.
Given structured data about a finished championship season, write a precise,
engaging review of how the drivers' championship was won and lost.
Use specific round numbers, race names, driver names, and points.
Avoid generic phrases.
Be precise and technically accurate.

The data comes from race results only: finishing positions, points,
retirements with their recorded cause, and finishing time gaps. It has NO
lap-by-lap, tire, weather, safety car, or team-radio data — do not mention,
guess at, or imply any of these. A "contender_duel" is two title contenders
finishing next to each other a few seconds apart: describe it as a close
fight to the flag, not as passes or laps you cannot see.

Championship positions and points after each round were computed from the
results, or, when "Dropped scores" says so, taken from the official
standings: in those seasons only a driver's best results counted, so a
driver's points total can be lower than the sum of their results, and the
title can go to the driver who scored fewer points in all.
"Quarters" split the season's rounds into four near-equal runs.

In the seasons before 1958 there was no constructors' championship, so the
constructors' standings are empty. Until 1960 the Indianapolis 500 was a
round of the championship, contested by its own American field; its winner
is not a Grand Prix winner in the European sense, and its drivers are
usually part-time drivers.

"Part-time drivers" started too few races to count as full-season drivers.
They are footnotes: never make them part of the championship story, and
mention them at most in one closing sentence of other_moments.

"Lineup changes" are facts from the entry lists about who drove for whom.
They carry no reasons: never guess at one (an injury, an illness, a driver
being dropped)."""

_REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A quick two-paragraph summary of the season: who won the title, how, and the story of the year.",
        },
        "championship_progression": {
            "type": "string",
            "description": "How the championship order evolved round by round, written to accompany a chart of each driver's championship position after every round: who led when, and where the decisive turns came.",
        },
        "quarterly_analysis": {
            "type": "string",
            "description": "The championship quarter by quarter, one short paragraph per quarter (Q1-Q4 as given): who led, who scored most, how the gap moved.",
        },
        "championship_moments": {
            "type": "string",
            "description": "The crucial moments for the title: lead changes, big points swings between the leading drivers (retirements, wins), close finishes between contenders, and where the title was decided.",
        },
        "other_moments": {
            "type": "string",
            "description": "Important moments outside the title fight: wins and first podiums for drivers outside the championship top five, rookies' first points, podiums and wins, and crucial points for midfield and backmarker teams.",
        },
        "driver_of_the_season": {
            "type": "string",
            "description": "A justified pick for driver of the season, with data evidence (points, wins, podiums, results against the car's standing). Full-season drivers only.",
        },
    },
    "required": [
        "summary",
        "championship_progression",
        "quarterly_analysis",
        "championship_moments",
        "other_moments",
        "driver_of_the_season",
    ],
    "additionalProperties": False,
}


# The early seasons had dozens of one-off entrants; listing every one would
# crowd out the season itself (and overflow Cerebras' small context).
_MAX_PART_TIME_DRIVERS = 12
_MAX_LINEUP_CHANGES = 20


def _capped(items: list, limit: int) -> list:
    return items if len(items) <= limit else items[:limit] + [f"... and {len(items) - limit} more"]


def _build_user_prompt(context: dict, positions_by_round: dict) -> str:
    decided = context['title_decided']
    part_timers = sorted(context['part_time_drivers'], key=lambda d: (-d['points'], -d['races']))
    when = (
        f"with {decided['rounds_left']} round(s) to go"
        if decided['rounds_left']
        else "at the final round"
    )
    return f"""
Season: {context['season']} Formula 1 World Championship, {context['rounds']} rounds
Title decided: {decided['driver_code']}, round {decided['round']} ({decided['race_name']}), {when}

Final Drivers' Standings: {compact(context['final_standings'])}
Final Constructors' Standings: {compact(context['constructor_standings'])}
Race Winners and Podiums: {compact(context['races'])}
Championship Position After Each Round (the season's top five, round 1 first): {compact(positions_by_round)}
Quarters: {compact(context['quarters'])}
Championship Moments: {compact(context['championship_moments'])}
Other Moments: {compact(context['other_moments'])}
Dropped scores (only best results counted; standings are official): {'yes' if context.get('official_standings_by_round') else 'no'}
Rookies: {compact(context['rookies'])}
Part-Time Drivers (footnotes only, highest scorers first): {compact(_capped([d['summary'] for d in part_timers], _MAX_PART_TIME_DRIVERS))}
Lineup Changes (no reasons given): {compact(_capped(context['lineup_changes'], _MAX_LINEUP_CHANGES))}

Write a full season review as a JSON object with these sections:
{section_guide(_REPORT_SCHEMA)}
"""


def generate_narrative(context: dict, positions_by_round: dict) -> dict:
    return generate_report(
        SYSTEM_PROMPT, _build_user_prompt(context, positions_by_round), "season_review", _REPORT_SCHEMA
    )
