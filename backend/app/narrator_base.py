"""
Shared LLM plumbing for the AI-written summaries (race and season): Gemini
first, Cerebras as the fallback.

Both providers are free tiers reached through their OpenAI-compatible
endpoints, so one client library covers both; only the base URL, key and
model differ. Each summarizer supplies its own prompts and JSON schema; this
module sends them and maps every failure onto NarrativeGenerationError
(retrying may help) or NarrativeUnavailableError (it will not).
"""
import json
import logging
import os
from dataclasses import dataclass

import openai
from openai import OpenAI

from .config import (
    CEREBRAS_BASE_URL,
    CEREBRAS_MODEL,
    GEMINI_BASE_URL,
    GEMINI_MODEL,
    NARRATIVE_TIMEOUT_SECONDS,
)
from .exceptions import NarrativeGenerationError, NarrativeUnavailableError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Provider:
    name: str
    model: str
    base_url: str
    api_key_env: str
    # Gemini is streamed, not a single blocking POST: a full report can
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


def compact(value) -> str:
    # Compact rather than indented: the indentation alone can double the
    # token count of a long list, and Cerebras' free-tier context is small
    # enough for that to matter.
    return json.dumps(value, separators=(",", ":"))


def section_guide(schema: dict) -> str:
    """One "- name: description" line per section, for the user prompt."""
    return "\n".join(f"- {name}: {spec['description']}" for name, spec in schema["properties"].items())


# 4xx the API will keep rejecting however many times we ask. 408/409/429 are
# the retryable exceptions to that: timeout, conflict, rate limit.
_RETRYABLE_CLIENT_ERRORS = {408, 409, 429}


def _is_permanent(status_code: int) -> bool:
    return 400 <= status_code < 500 and status_code not in _RETRYABLE_CLIENT_ERRORS


def _generate_with(provider: _Provider, system_prompt: str, user_prompt: str, schema_name: str, schema: dict) -> dict:
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
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
        # The report is a rewrite of structured data we've already computed,
        # not open-ended analysis, so heavy reasoning buys latency and tokens
        # we don't need. Raise it if the narratives get thin.
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

    sections = schema["required"]
    if not isinstance(report, dict) or not all(
        isinstance(report.get(name), str) and report[name].strip() for name in sections
    ):
        raise NarrativeGenerationError(f"{provider.name} returned a report with missing sections.")

    return {name: report[name] for name in sections}


def generate_report(system_prompt: str, user_prompt: str, schema_name: str, schema: dict) -> dict:
    """The report's sections, from the first provider that writes a complete one."""
    errors: list[NarrativeGenerationError] = []
    for provider in _PROVIDERS:
        try:
            return _generate_with(provider, system_prompt, user_prompt, schema_name, schema)
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
