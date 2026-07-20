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
