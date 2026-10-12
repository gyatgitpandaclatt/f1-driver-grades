from datetime import datetime, timezone

# SEASONS — LIVE, NOTHING TO UPDATE EACH YEAR
#
# The current season is the calendar year. Before a year's first race it has
# no completed rounds, which the API already answers as a "no data yet" empty
# state, and the previous seasons stay one click away in the season selector.
#
# PREVIOUS_SEASONS is how far back the selector reaches. Each finished season
# costs a few dozen upstream requests the first time it is opened (then it is
# kept for the life of the process — see cache_base.SeasonCache), so widening
# the window is cheap until someone opens the older seasons.
PREVIOUS_SEASONS = 5


def current_season() -> int:
    return datetime.now(timezone.utc).year


def available_seasons() -> list[int]:
    """The seasons the API serves, newest first: this year and the previous ones."""
    current = current_season()
    return list(range(current, current - PREVIOUS_SEASONS - 1, -1))


def is_completed_season(season: int) -> bool:
    """A season before this year is over: its results will never change."""
    return season < current_season()


# Drivers who started fewer than this share of the season's completed rounds
# are left out of the grades, and never anyone with fewer than
# MIN_RACES_FOR_GRADE. A stand-in has nowhere near enough data for a season
# grade, and their volatile per-race numbers would skew both the model and
# the score normalisation for everyone else. The bar is a share rather than a
# fixed count because a fixed count stops working as the season goes on: by
# mid-season a reserve who filled in for two races clears a bar of two and is
# graded on a tenth of everyone else's sample.
MIN_RACE_SHARE_FOR_GRADE = 0.5
MIN_RACES_FOR_GRADE = 2

# A driver is a rookie until they have ROOKIE_SEASON_THRESHOLD full seasons
# behind them, counted from their career before the season being graded. A
# season only counts as full if they started at least
# ROOKIE_FULL_SEASON_RACE_SHARE of its races — the same bar as being graded —
# so a reserve's stand-in outings don't use up their rookie year: a driver
# who subbed for three races last year and races full-time this year is
# still a rookie. Raise the threshold to 2 to count second-year drivers too.
ROOKIE_SEASON_THRESHOLD = 1
ROOKIE_FULL_SEASON_RACE_SHARE = MIN_RACE_SHARE_FOR_GRADE

# Lower tier number = stronger car. A constructor's tier comes from where it
# sits in that season's constructors' championship (the final order for a
# finished season, the order so far for the current one), so it updates by
# itself every season and every round. Each entry is (lowest championship
# position, tier): P1 is tier 1, P2 tier 1.5, P3-P4 tier 2, and so on;
# anyone below the last entry is LOWEST_CONSTRUCTOR_TIER. Early in a season
# the order rests on a handful of races, so expect tiers to move.
CONSTRUCTOR_TIER_BY_POSITION = [
    (1, 1),
    (2, 1.5),
    (4, 2),
    (6, 2.5),
    (8, 3),
]
LOWEST_CONSTRUCTOR_TIER = 4
# For a constructor missing from the standings altogether.
DEFAULT_CONSTRUCTOR_TIER = 2

TIER_BONUS = {1: 0, 1.5: 1, 2: 2, 2.5: 3, 3: 4, 4: 6}
DEFAULT_TIER_BONUS = 2


SEASON_FEATURE_COLS = [
    "races",
    "avg_finish_minus_grid",
    "overperf_share",
    "underperf_share",
    "is_rookie",
]

API_BASE_URL = "https://api.jolpi.ca/ergast/f1"
CACHE_TTL_SECONDS = 20 * 60
REQUEST_TIMEOUT = 10

# Jolpica documents a maximum page size of 100 and silently caps anything
# larger, which the paginators handle by striding by the rows they actually
# received. So a race's laps.json (~20 drivers x ~60 laps = ~1200 timing
# rows) still costs ~12 round trips, and a season's results ~5. Combined with
# the 500 requests/hour limit, that is why nothing season-wide reads lap data.
PAGE_LIMIT = 1000

# Upstream politeness/resilience: Jolpica rate-limits unauthenticated callers
# (burst + hourly), and a 429 is a "come back shortly", not a bad gateway.
MAX_UPSTREAM_RETRIES = 3
UPSTREAM_BACKOFF_BASE_SECONDS = 1.0
UPSTREAM_MAX_CONCURRENCY = 3
DEFAULT_RETRY_AFTER_SECONDS = 30

# Ceilings on a provider-supplied Retry-After. The provider controls that
# header, so treat it as untrusted input: clamp what we pass on to the client,
# and never block a request thread for longer than MAX_RETRY_SLEEP_SECONDS —
# a longer wait is handed to the client as a 503 + Retry-After instead, which
# is the whole point of answering 503 rather than sitting on the connection.
MAX_RETRY_AFTER_SECONDS = 300
MAX_RETRY_SLEEP_SECONDS = 30

# Race summarizer (Jolpica/Ergast + LLM narrative) — a completed race's
# data never changes, so this cache can be long-lived; recomputation costs an
# LLM call, not just an API round trip.
RACE_SUMMARY_CACHE_TTL_SECONDS = 6 * 60 * 60

# Raw per-round race data (results/laps/pit stops). A finished race's data
# never changes, so a round we've seen complete data for is cached for the
# process's lifetime — repeat visitors cost zero upstream requests. A round
# whose lap data hasn't been published yet is only held briefly so we pick
# the rest of it up soon after it lands.
ROUND_CACHE_MAX_ROUNDS = 8
INCOMPLETE_ROUND_CACHE_TTL_SECONDS = 10 * 60

# Narrative providers, tried in order: Gemini (Google AI Studio free tier)
# first, Cerebras as the fallback when Gemini is unconfigured, rate limited,
# or down. Both are called through their OpenAI-compatible endpoints. Keys
# come from GEMINI_API_KEY / CEREBRAS_API_KEY; a provider without a key is
# skipped.
GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
CEREBRAS_MODEL = "gpt-oss-120b"
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"

# Ceiling on one narrative call. Gemini is streamed, so for it this is a real
# stall detector rather than "how long may a slow generation take" — it stops
# a wedged call from pinning the cache's single-flight lock.
NARRATIVE_TIMEOUT_SECONDS = 180.0

# Lineup changes (stand-ins, swaps, mid-season replacements) are detected
# from the entry lists by app/lineups.py, for every season, with nothing to
# maintain here: a race report is told who drove for whom and whose seat
# they were in, and the season summary footnotes every part-time driver.
#
# What the data can never say is *why* a lineup changed. These optional
# reasons fill that in. A reason is attached only when that season's own
# entry list shows the driver at that constructor, so it cannot leak into a
# season or a race it does not apply to. The stated reason is not verified;
# only the pairing is matched.
LINEUP_CHANGE_REASONS = [
    {
        "season": 2026,
        "driver_code": "LAW",
        "constructor": "Red Bull",
        "reason": "Lawson was standing in for Isack Hadjar, who was injured.",
    },
]

# Season summarizer (finished seasons only; the current one has the race
# summary). See season_summary/ for how each threshold is used.
#
# Title contenders: the top N of the championship going into a round (for
# round 1, the season's final top N). Their points swings and close finishes
# are the championship's crucial moments.
SEASON_SUMMARY_TITLE_CONTENDERS = 3
# Points gained on a rival in one weekend (race + sprint) that count as a
# swing, when they come from the gainer winning or the rival retiring: a win
# against a rival's P5, or any retirement against a podium.
SEASON_SUMMARY_SWING_MIN_POINTS = 15
# Two contenders finishing next to each other within this many seconds were
# fighting to the flag. There's no lap data season-wide (see PAGE_LIMIT), so
# this — from the finishing times — is how a battle is recognised.
SEASON_SUMMARY_CLOSE_FINISH_SECONDS = 3.0
# Drivers outside this top N of the final championship count as
# "non-championship" drivers, whose wins and first podiums are moments.
SEASON_SUMMARY_CHAMPIONSHIP_DRIVERS = 5
# Constructors from this championship position down are the midfield and
# backmarkers, whose points can be crucial.
SEASON_SUMMARY_MIDFIELD_FROM_POSITION = 5
# A weekend's points are crucial for such a team when they are at least this
# share of its season total, or its first points after a pointless first
# quarter of the season.
SEASON_SUMMARY_CRUCIAL_POINTS_SHARE = 0.25
# Caps on what the narrator is handed, to keep the prompt inside Cerebras'
# small free-tier context.
SEASON_SUMMARY_MAX_TITLE_MOMENTS = 12
SEASON_SUMMARY_MAX_OTHER_MOMENTS = 15
