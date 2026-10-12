"""
Saved snapshots of finished seasons, and the script that writes them.

A finished season's grades and season summary never change, yet computing
one costs a few dozen upstream requests, an LLM call for the summary, and
several seconds of model fitting. On a host that scales to zero (Cloud
Run), the in-memory caches start empty on every cold start, so that cost
comes back again and again. A snapshot is the same response, computed once
and committed under backend/snapshots/: the site serves it without
touching Jolpica or the LLM.

Write or refresh them from backend/, on a machine that can reach Jolpica
(and with GEMINI_API_KEY or CEREBRAS_API_KEY set, for the summaries):

    python -m app.snapshots              # every finished season on offer
    python -m app.snapshots 2024 2025    # just these
    python -m app.snapshots --force      # rebuild existing ones too

then commit backend/snapshots/*.json. A season without a snapshot is
computed live, as before. So is one whose snapshot no longer matches the
response schema (after a field is added, say): it is logged and ignored
until the script is run again with --force.
"""
import argparse
import functools
import json
import logging
import sys
import time
from pathlib import Path
from typing import Callable

from .config import available_seasons, is_completed_season
from .exceptions import NarrativeUnavailableError, UpstreamRateLimitedError
from .pipeline import run_pipeline
from .schemas import DriverGradesResponse
from .season_summary.models import SeasonSummaryResponse
from .season_summary.pipeline import run_season_summary_pipeline

logger = logging.getLogger("f1_driver_grades")

SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "snapshots"

# kind -> (response model, live compute)
KINDS = {
    "driver_grades": (DriverGradesResponse, run_pipeline),
    "season_summary": (SeasonSummaryResponse, run_season_summary_pipeline),
}


def snapshot_path(kind: str, season: int) -> Path:
    return SNAPSHOT_DIR / f"{kind}_{season}.json"


def load_snapshot(kind: str, season: int) -> dict | None:
    """The saved response for a finished season, or None to compute it live."""
    # The current season changes every race weekend; a snapshot of it would
    # freeze it.
    if not is_completed_season(season):
        return None
    path = snapshot_path(kind, season)
    if not path.is_file():
        return None
    model, _ = KINDS[kind]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        model.model_validate(data)
        if data.get("season") != season:
            raise ValueError(f"it holds season {data.get('season')}")
    # JSONDecodeError and pydantic's ValidationError are both ValueErrors.
    except (OSError, ValueError) as exc:
        logger.warning("Ignoring snapshot %s (%s); computing the season live instead.", path.name, exc)
        return None
    data["snapshot"] = True
    return data


def prefer_snapshot(kind: str, compute: Callable[[int], dict]) -> Callable[[int], dict]:
    """`compute`, but served from the season's snapshot when there is one."""
    @functools.wraps(compute)
    def wrapper(season: int) -> dict:
        return load_snapshot(kind, season) or compute(season)
    return wrapper


# --- the script ---------------------------------------------------------------

# Jolpica answers a burst with 429 + Retry-After; a run over several seasons
# can trip it. Each wait resumes cheaply: what a season already fetched is
# kept in memory (see data_fetch), so only the rest is asked for again.
_MAX_RATE_LIMIT_WAITS = 5


def _build(kind: str, season: int) -> dict:
    model, compute = KINDS[kind]
    for attempt in range(_MAX_RATE_LIMIT_WAITS + 1):
        try:
            data = compute(season)
            break
        except UpstreamRateLimitedError as exc:
            if attempt == _MAX_RATE_LIMIT_WAITS:
                raise
            print(f"  rate limited by the F1 data provider; waiting {exc.retry_after}s", flush=True)
            time.sleep(exc.retry_after)
    # Written through the response model, so what is saved is exactly what
    # the API would serve and is certain to load back.
    return model.model_validate(data).model_dump(mode="json", exclude={"snapshot"})


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".json.partial")
    partial.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    partial.replace(path)


def main(argv: list[str] | None = None) -> int:
    finished = sorted(s for s in available_seasons() if is_completed_season(s))
    parser = argparse.ArgumentParser(
        prog="python -m app.snapshots",
        description="Save finished seasons' grades and season summaries for the site to serve.",
    )
    parser.add_argument(
        "seasons", nargs="*", type=int,
        help=f"finished seasons to save (default: all of {', '.join(map(str, finished))})",
    )
    parser.add_argument("--force", action="store_true", help="rebuild snapshots that already exist")
    parser.add_argument(
        "--grades-only", action="store_true",
        help="skip the season summaries, which need GEMINI_API_KEY or CEREBRAS_API_KEY",
    )
    args = parser.parse_args(argv)

    seasons = sorted(set(args.seasons)) or finished
    unavailable = [s for s in seasons if s not in finished]
    if unavailable:
        parser.error(
            f"{', '.join(map(str, unavailable))}: not a finished season the site offers "
            f"(choose from {', '.join(map(str, finished))})"
        )

    logging.basicConfig(level=logging.WARNING, format="  %(levelname)s %(name)s: %(message)s")
    logger.setLevel(logging.INFO)  # upstream retries, for a run that pauses

    kinds = ["driver_grades"] if args.grades_only else ["driver_grades", "season_summary"]
    failed = 0
    summaries_unavailable = False
    for season in seasons:
        for kind in kinds:
            label = f"{season} {kind.replace('_', ' ')}"
            path = snapshot_path(kind, season)
            if path.exists() and not args.force:
                print(f"{label}: already saved, skipping (--force rebuilds it)")
                continue
            if kind == "season_summary" and summaries_unavailable:
                failed += 1
                print(f"{label}: skipped, the narrative is unavailable (see above)")
                continue
            print(f"{label}: building…", flush=True)
            started = time.monotonic()
            try:
                data = _build(kind, season)
            except NarrativeUnavailableError as exc:
                # No key, a rejected key: every other summary would fail the
                # same way, so don't spend upstream requests finding out.
                failed += 1
                summaries_unavailable = True
                print(
                    f"{label}: FAILED, the narrative is unavailable ({exc}). Set GEMINI_API_KEY "
                    "or CEREBRAS_API_KEY in backend/.env, or pass --grades-only."
                )
                continue
            except Exception as exc:
                failed += 1
                print(f"{label}: FAILED ({type(exc).__name__}: {exc})")
                continue
            _write(path, data)
            print(f"{label}: saved {path} in {time.monotonic() - started:.0f}s")

    if failed:
        print(f"{failed} snapshot(s) not saved; rerun to retry them (saved ones are skipped).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
