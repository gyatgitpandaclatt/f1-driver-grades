"""
Convert structured race event data into a natural-language race narrative via
an LLM: Gemini first, Cerebras as the fallback.

Both providers are free tiers reached through their OpenAI-compatible
endpoints, so one client library covers both; only the base URL, key and
model differ.
"""
import json
import logging
import os
from dataclasses import dataclass

import openai
from openai import OpenAI

from ..config import (
    CEREBRAS_BASE_URL,
    CEREBRAS_MODEL,
    GEMINI_BASE_URL,
    GEMINI_MODEL,
    NARRATIVE_TIMEOUT_SECONDS,
)
from ..exceptions import NarrativeGenerationError, NarrativeUnavailableError

logger = logging.getLogger(__name__)

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
car and why, supplied because the results feed does not carry that context.
Work them into the report where they matter to the story. Do not infer any
other lineup change, injury, or substitution beyond the notes given."""

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

_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {"name": "race_report", "strict": True, "schema": _REPORT_SCHEMA},
}


@dataclass(frozen=True)
class _Provider:
    name: str
    model: str
    base_url: str
    api_key_env: str
    # Gemini is streamed, not a single blocking POST: a full race report can
    # take a while, and a non-streaming request that long is what hosting
    # proxies cut off — the connection dies mid-flight and the browser gets a
    # non-JSON error page instead of a report. Cerebras generates at thousands
    # of tokens a second, so a plain request returns well inside that window.
    stream: bool
    # None leaves the output budget to the provider: Cerebras' free tier caps
    # the whole context (prompt + output) at a few thousand tokens, and asking
    # for more than is left is rejected outright.
    max_tokens: int | None


_PROVIDERS = (
    _Provider("Gemini", GEMINI_MODEL, GEMINI_BASE_URL, "GEMINI_API_KEY", stream=True, max_tokens=16000),
    _Provider("Cerebras", CEREBRAS_MODEL, CEREBRAS_BASE_URL, "CEREBRAS_API_KEY", stream=False, max_tokens=None),
)


def _compact(value) -> str:
    # Compact rather than indented: the indentation alone can double the
    # token count of a long overtake list, and Cerebras' free-tier context is
    # small enough for that to matter.
    return json.dumps(value, separators=(",", ":"))


def _build_user_prompt(context: dict) -> str:
    lineup_notes = context.get('lineup_notes') or []
    lineup_section = (
        "Lineup Notes:\n" + "\n".join(f"- {note}" for note in lineup_notes) + "\n\n"
        if lineup_notes
        else ""
    )
    section_guide = "\n".join(
        f"- {name}: {spec['description']}" for name, spec in _REPORT_SCHEMA["properties"].items()
    )
    return f"""
Race: {context['race_name']}, {context['year']}
Laps: {context['total_laps']}

{lineup_section}Final Classification (classified runners only): {_compact(context['final_classification'])}
Retirements (did not finish; "status" is the recorded cause): {_compact(context.get('retirements', []))}
Pit Stops: {_compact(context['pit_stops'])}
Overtakes: {_compact(context['overtakes'])}
Battle Highlights: {_compact(context['battles'])}

Write a full race report as a JSON object with these sections:
{section_guide}
"""


# 4xx the API will keep rejecting however many times we ask. 408/409/429 are
# the retryable exceptions to that: timeout, conflict, rate limit.
_RETRYABLE_CLIENT_ERRORS = {408, 409, 429}


def _is_permanent(status_code: int) -> bool:
    return 400 <= status_code < 500 and status_code not in _RETRYABLE_CLIENT_ERRORS


def _generate_with(provider: _Provider, user_prompt: str) -> dict:
    api_key = os.getenv(provider.api_key_env)
    if not api_key:
        raise NarrativeUnavailableError(f"{provider.api_key_env} is not configured in this environment.")

    # One retry, not the SDK's default two: when this provider is rate
    # limited or out of daily quota, the next provider is a better bet than
    # waiting out another backoff.
    client = OpenAI(
        api_key=api_key,
        base_url=provider.base_url,
        timeout=NARRATIVE_TIMEOUT_SECONDS,
        max_retries=1,
    )
    request = {
        "model": provider.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": _RESPONSE_FORMAT,
        # The report is a rewrite of structured data we've already computed
        # (classification, stops, overtakes, battles), not open-ended
        # analysis, so heavy reasoning buys latency and tokens we don't need.
        # Raise it if the narratives get thin.
        "reasoning_effort": "low",
    }
    if provider.max_tokens is not None:
        request["max_tokens"] = provider.max_tokens

    try:
        if provider.stream:
            parts = []
            finish_reason = None
            with client.chat.completions.create(**request, stream=True) as stream:
                for chunk in stream:
                    if not chunk.choices:
                        continue
                    choice = chunk.choices[0]
                    if choice.delta.content:
                        parts.append(choice.delta.content)
                    if choice.finish_reason:
                        finish_reason = choice.finish_reason
            content = "".join(parts)
        else:
            response = client.chat.completions.create(**request)
            choice = response.choices[0]
            content = choice.message.content or ""
            finish_reason = choice.finish_reason
    except openai.APIConnectionError as exc:
        raise NarrativeGenerationError(f"Could not reach the {provider.name} API: {exc}") from exc
    except openai.APIStatusError as exc:
        # A rejected key is a 401/403, an unknown model a 404, a prompt over
        # the context limit a 400 — none improves by asking again. An
        # exhausted free-tier quota is a 429 and clears on its own.
        if _is_permanent(exc.status_code):
            raise NarrativeUnavailableError(f"{provider.name} API error: {exc}") from exc
        raise NarrativeGenerationError(f"{provider.name} API error: {exc}") from exc
    except openai.APIError as exc:
        # An error event mid-stream carries no HTTP status.
        raise NarrativeGenerationError(f"{provider.name} API error: {exc}") from exc

    if finish_reason == "content_filter":
        # A refusal of this input will be refused again.
        raise NarrativeUnavailableError(f"{provider.name} declined to write this report.")
    if finish_reason == "length":
        raise NarrativeGenerationError(f"{provider.name} ran out of output tokens before finishing the report.")

    try:
        report = json.loads(content)
    except json.JSONDecodeError as exc:
        raise NarrativeGenerationError(f"{provider.name} did not return a JSON report: {exc}") from exc

    sections = _REPORT_SCHEMA["required"]
    if not isinstance(report, dict) or not all(
        isinstance(report.get(name), str) and report[name].strip() for name in sections
    ):
        raise NarrativeGenerationError(f"{provider.name} returned a report with missing sections.")

    return {name: report[name] for name in sections}


def generate_narrative(context: dict) -> dict:
    user_prompt = _build_user_prompt(context)
    errors: list[NarrativeGenerationError] = []
    for provider in _PROVIDERS:
        try:
            return _generate_with(provider, user_prompt)
        except NarrativeGenerationError as exc:
            logger.warning("%s narrative failed: %s", provider.name, exc)
            errors.append(exc)

    # Only tell the visitor retrying is pointless when every provider failed
    # for a reason that needs the operator (no key, bad key, refusal). If any
    # failure was transient — a rate limit, an outage — a later try may work.
    detail = " | ".join(str(exc) for exc in errors)
    if all(isinstance(exc, NarrativeUnavailableError) for exc in errors):
        raise NarrativeUnavailableError(detail)
    raise NarrativeGenerationError(detail)
