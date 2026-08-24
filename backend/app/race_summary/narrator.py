"""
Convert structured race event data into a natural-language race narrative via Claude.
"""
import json

import anthropic
from anthropic import Anthropic

from ..config import ANTHROPIC_MODEL, NARRATIVE_TIMEOUT_SECONDS
from ..exceptions import NarrativeGenerationError

SYSTEM_PROMPT = """You are a professional Formula 1 race analyst and journalist.
Given structured race data, write a detailed, engaging race report in the style of
Autosport or The Race.
Use specific lap numbers, driver names, and time gaps.
Avoid generic phrases.
Be precise and technically accurate.

The data provided does NOT include tire compounds, weather, or safety car/VSC
periods — do not mention, guess at, or imply any of these (e.g. don't say a
stop was "onto softs" or a gap opened up "under the safety car"). Ground pit
stop analysis in lap number and stop duration only."""

_SECTION_TOOL = {
    "name": "submit_race_report",
    "description": "Submit the finished race report, broken into its sections.",
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
    },
}


def _build_user_prompt(context: dict) -> str:
    return f"""
Race: {context['race_name']}, {context['year']}
Laps: {context['total_laps']}

Final Classification: {json.dumps(context['final_classification'], indent=2)}
Pit Stops: {json.dumps(context['pit_stops'], indent=2)}
Overtakes: {json.dumps(context['overtakes'], indent=2)}
Battle Highlights: {json.dumps(context['battles'], indent=2)}

Write a full race report and submit it via the submit_race_report tool.
"""


def generate_narrative(context: dict) -> dict:
    # Constructed lazily (rather than at module import time) so a missing
    # ANTHROPIC_API_KEY surfaces as a clear NarrativeGenerationError on the
    # first request instead of crashing the whole race_summary import chain
    # at startup with an unrelated-looking error.
    client = Anthropic(timeout=NARRATIVE_TIMEOUT_SECONDS)
    user_prompt = _build_user_prompt(context)
    try:
        # Streamed, not a single blocking POST: a full race report is a
        # minutes-long generation, and a non-streaming request that long is
        # what hosting proxies cut off — the connection dies mid-flight and
        # the browser gets a non-JSON error page instead of a report.
        # Streaming keeps bytes flowing; get_final_message() still hands back
        # the assembled response, so nothing downstream changes.
        #
        # effort=medium: the report is a rewrite of structured data we've
        # already computed (classification, stops, overtakes, battles), not
        # open-ended analysis, so the default (high) buys latency we don't
        # need here. Raise it if the narratives get thin.
        with client.messages.stream(
            model=ANTHROPIC_MODEL,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            output_config={"effort": "medium"},
            tools=[_SECTION_TOOL],
            tool_choice={"type": "tool", "name": "submit_race_report"},
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            response = stream.get_final_message()
    except anthropic.APIConnectionError as exc:
        raise NarrativeGenerationError(f"Could not reach the Claude API: {exc}") from exc
    except anthropic.APIStatusError as exc:
        raise NarrativeGenerationError(f"Claude API error: {exc}") from exc
    except TypeError as exc:
        # With no credentials configured anywhere (no ANTHROPIC_API_KEY, no
        # auth token, no profile), the SDK doesn't fail at Anthropic() — it
        # defers the check until the request is built and raises a plain
        # TypeError from _validate_headers, not an anthropic.* exception.
        if "authentication" not in str(exc).lower():
            raise
        raise NarrativeGenerationError(
            "ANTHROPIC_API_KEY is not configured in this environment."
        ) from exc

    if response.stop_reason == "refusal":
        raise NarrativeGenerationError("The narrative generator declined to write this report.")

    tool_use = next((block for block in response.content if block.type == "tool_use"), None)
    if tool_use is None:
        raise NarrativeGenerationError("The narrative generator did not return a structured report.")

    return tool_use.input
