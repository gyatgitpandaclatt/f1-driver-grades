"""
Convert structured race event data into a natural-language race narrative via Claude.
"""
import json

import anthropic
from anthropic import Anthropic

from ..config import ANTHROPIC_MODEL
from ..exceptions import NarrativeGenerationError

client = Anthropic()

SYSTEM_PROMPT = """You are a professional Formula 1 race analyst and journalist.
Given structured race data, write a detailed, engaging race report in the style of
Autosport or The Race.
Use specific lap numbers, driver names, and time gaps.
Avoid generic phrases.
Be precise and technically accurate."""

_SECTION_TOOL = {
    "name": "submit_race_report",
    "description": "Submit the finished race report, broken into its six sections.",
    "strict": True,
    "input_schema": {
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
                "description": "Strategy breakdown for the top 5 finishers.",
            },
            "overtakes_battles": {
                "type": "string",
                "description": "The most significant position fights of the race.",
            },
            "telemetry_spotlight": {
                "type": "string",
                "description": "One driver's standout telemetry data point.",
            },
            "driver_of_the_day": {
                "type": "string",
                "description": "A justified pick with data evidence, contrasted with the actual voted Driver of the Day.",
            },
        },
        "required": [
            "summary",
            "lap_highlights",
            "pit_analysis",
            "overtakes_battles",
            "telemetry_spotlight",
            "driver_of_the_day",
        ],
        "additionalProperties": False,
    },
}


def _build_user_prompt(context: dict) -> str:
    return f"""
Race: {context['race_name']}, {context['year']}
Laps: {context['total_laps']}
Weather: {context['weather_summary']}

Final Classification: {json.dumps(context['final_classification'], indent=2)}
Pit Stops: {json.dumps(context['pit_stops'], indent=2)}
Overtakes: {json.dumps(context['overtakes'], indent=2)}
Key Events: {json.dumps(context['key_events'], indent=2)}
Tire Strategies: {json.dumps(context['strategies'], indent=2)}
Battle Highlights: {json.dumps(context['battles'], indent=2)}
Telemetry Highlights: {json.dumps(context['telemetry_highlights'], indent=2)}

Write a full race report and submit it via the submit_race_report tool.
"""


def generate_narrative(context: dict) -> dict:
    user_prompt = _build_user_prompt(context)
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            tools=[_SECTION_TOOL],
            tool_choice={"type": "tool", "name": "submit_race_report"},
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.APIConnectionError as exc:
        raise NarrativeGenerationError(f"Could not reach the Claude API: {exc}") from exc
    except anthropic.APIStatusError as exc:
        raise NarrativeGenerationError(f"Claude API error: {exc}") from exc

    if response.stop_reason == "refusal":
        raise NarrativeGenerationError("The narrative generator declined to write this report.")

    tool_use = next((block for block in response.content if block.type == "tool_use"), None)
    if tool_use is None:
        raise NarrativeGenerationError("The narrative generator did not return a structured report.")

    return tool_use.input
