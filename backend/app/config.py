#
# SEASON-SPECIFIC — UPDATE EACH YEAR
SEASON = 2026

# Driver codes for drivers in their first full F1 season this year.
ROOKIES = {"LIN"}

# Lower tier number = stronger car. Unlisted constructors default to
# DEFAULT_CONSTRUCTOR_TIER below.
CONSTRUCTOR_TIER = {
    "Mercedes": 1,
    "Ferrari": 1.5,
    "McLaren": 2,
    "Red Bull": 2,
    "Alpine F1 Team": 2.5,
    "RB F1 Team": 2.5,
    "Haas F1 Team": 3,
    "Williams": 3,
    "Audi": 3,
    "Aston Martin": 4,
    "Cadillac F1 Team": 4,
}
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

# Jolpica's documented maximum page size. A race's laps.json is ~20 drivers x
# ~60 laps = ~1200 timing rows, so at the old limit of 100 a single race cost
# ~12 sequential round trips; at 1000 it costs 2.
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

# Race summarizer (Jolpica/Ergast + Claude narrative) — a completed race's
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

ANTHROPIC_MODEL = "claude-opus-5"

# Ceiling on one narrative call. Streamed, so this is a real stall detector
# rather than "how long may a slow generation take" — it stops a wedged call
# from pinning the cache's single-flight lock.
NARRATIVE_TIMEOUT_SECONDS = 180.0
