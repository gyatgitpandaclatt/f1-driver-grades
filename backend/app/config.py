import os

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
PAGE_LIMIT = 100

# Race summarizer (FastF1 + Claude narrative) — a completed race's data never
# changes, so this cache can be long-lived; recomputation is expensive (FastF1
# telemetry download + an LLM call), not just an API round trip.
RACE_SUMMARY_CACHE_TTL_SECONDS = 6 * 60 * 60
FASTF1_CACHE_DIR = "fastf1_cache"
ANTHROPIC_MODEL = "claude-opus-5"

# FastF1's live-timing data source blocks requests from Replit's IP ranges
# (both the dev workspace and deployments) as an anti-scraping measure, so
# the feature can never work there — REPL_ID is set by Replit in both.
RACE_SUMMARY_AVAILABLE = os.environ.get("REPL_ID") is None
