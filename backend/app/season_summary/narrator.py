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
results. "Quarters" split the season's rounds into four near-equal runs.

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


def _build_user_prompt(context: dict, positions_by_round: dict) -> str:
    decided = context['title_decided']
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
Rookies: {compact(context['rookies'])}
Part-Time Drivers (footnotes only): {compact([d['summary'] for d in context['part_time_drivers']])}
Lineup Changes (no reasons given): {compact(context['lineup_changes'])}

Write a full season review as a JSON object with these sections:
{section_guide(_REPORT_SCHEMA)}
"""


def generate_narrative(context: dict, positions_by_round: dict) -> dict:
    return generate_report(
        SYSTEM_PROMPT, _build_user_prompt(context, positions_by_round), "season_review", _REPORT_SCHEMA
    )
