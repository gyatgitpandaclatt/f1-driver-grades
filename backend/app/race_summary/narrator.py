"""
Convert structured race event data into a natural-language race narrative via
an LLM (Gemini first, Cerebras as the fallback — see narrator_base).
"""
from ..narrator_base import compact, generate_report, section_guide

SYSTEM_PROMPT = """You are a professional Formula 1 race analyst and journalist.
Given structured race data, write a detailed, engaging race report in the style of
Autosport or The Race.
Use specific lap numbers, driver names, and time gaps.
Avoid generic phrases.
Be precise and technically accurate.

The data provided does NOT include tire compounds, weather, or safety car/VSC
periods — do not mention, guess at, or imply any of these (e.g. don't say a
stop was "onto softs" or a gap opened up "under the safety car"). Ground pit
stop analysis in lap number and stop duration only.

"Retirements" is the complete list of drivers who did not finish, with the
cause recorded by the results feed and the number of laps they completed.
"Final Classification" holds classified runners only, so never infer the
retirements from it or describe a classified driver as the race's only
retirement.

Any "Lineup Notes" in the race data are verified facts about who drove which
car, taken from the season's entry lists, because the race data alone does
not make a lineup change obvious. Work them into the report where they
matter to the story. A note gives the reason for a change only when one is
known: never guess at one it does not state (an injury, an illness, a driver
being dropped), and do not infer any other lineup change beyond the notes
given."""

_REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "2-3 paragraph overview of the race.",
        },
        "lap_highlights": {
            "type": "string",
            "description": "Key moments by phase: start, early, mid, late.",
        },
        "pit_analysis": {
            "type": "string",
            "description": "Pit stop timing and its impact on track position for the top 5 finishers (lap number and duration only — no tire compound data is available).",
        },
        "overtakes_battles": {
            "type": "string",
            "description": "The most significant position fights of the race.",
        },
        "driver_of_the_day": {
            "type": "string",
            "description": "A justified pick with data evidence (positions gained, overtakes made, battles won).",
        },
    },
    "required": [
        "summary",
        "lap_highlights",
        "pit_analysis",
        "overtakes_battles",
        "driver_of_the_day",
    ],
    "additionalProperties": False,
}


def _build_user_prompt(context: dict) -> str:
    lineup_notes = context.get('lineup_notes') or []
    lineup_section = (
        "Lineup Notes:\n" + "\n".join(f"- {note}" for note in lineup_notes) + "\n\n"
        if lineup_notes
        else ""
    )
    return f"""
Race: {context['race_name']}, {context['year']}
Laps: {context['total_laps']}

{lineup_section}Final Classification (classified runners only): {compact(context['final_classification'])}
Retirements (did not finish; "status" is the recorded cause): {compact(context.get('retirements', []))}
Pit Stops: {compact(context['pit_stops'])}
Overtakes: {compact(context['overtakes'])}
Battle Highlights: {compact(context['battles'])}

Write a full race report as a JSON object with these sections:
{section_guide(_REPORT_SCHEMA)}
"""


def generate_narrative(context: dict) -> dict:
    return generate_report(SYSTEM_PROMPT, _build_user_prompt(context), "race_report", _REPORT_SCHEMA)
