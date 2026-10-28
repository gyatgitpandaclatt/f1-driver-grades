from datetime import datetime, timezone

# SEASONS — LIVE, NOTHING TO UPDATE EACH YEAR
#
# The current season is the calendar year. Before a year's first race it has
# no completed rounds, which the API already answers as a "no data yet" empty
# state, and the previous seasons stay one click away in the season selector.
#
# FIRST_SEASON is how far back the selector reaches: 2003, the first season
# with qualifying data for every round and every driver. Before it the data
# has qualifying for only some rounds (1994-2002) or none at all, and the
# grid would have to stand in for it in the qualifying score and the
# head-to-head. Each finished season costs a few dozen upstream requests the
# first time it is opened (then it is kept for the life of the process — see
# cache_base.SeasonCache); saved snapshots (snapshots.py) remove even that.
#
# The code also handles every earlier season Jolpica carries, back to 1950,
# should FIRST_SEASON ever be lowered: the grid stands in for missing
# qualifying, there was no constructors' championship before 1958 (tiers
# come from the constructors' points instead), dropped scores until 1990,
# the Indianapolis 500 as a round until 1960, and no three-letter code for
# most drivers before the mid-2000s (one is made up from the surname, which
# 2003-2004 still need). See data_fetch.py, pipeline.py, career.py and
# season_summary/.
FIRST_SEASON = 2003
# The first World Championship, which careers and rookie checks reach back
# to whatever the selector offers: a 2003 rookie check reads 2002's results.
FIRST_CHAMPIONSHIP_SEASON = 1950
# Sprints began in 2021, the constructors' championship in 1958; earlier
# seasons skip asking for them.
FIRST_SPRINT_SEASON = 2021
FIRST_CONSTRUCTORS_SEASON = 1958
# Until this season only a constructor's best-placed car scored for it in
# the constructors' championship; from the next, every car's points count.
LAST_BEST_CAR_ONLY_SEASON = 1978

# The Indianapolis 500 was a round of the championship from 1950 to 1960,
# contested by its own American field. Its one-off entrants are folded into a
# single footnote, and it doesn't count towards the grading bar: a Grand Prix
# regular who skipped Indianapolis still raced the whole season.
INDIANAPOLIS_500 = "Indianapolis 500"


def is_indianapolis_500(race_name: str) -> bool:
    return race_name == INDIANAPOLIS_500


# Dropped scores. Until 1990 only a driver's best results counted, by the
# rules below (the same table Jolpica computes its standings from:
# jolpica/formula_one/fixtures/championship_systems.json). Each season maps to
# (split, best): split 0 counts the season as one, "front" splits it in halves
# with the odd round in the first, "back" with the odd round in the second;
# best is the results counted in each part, or "all_but_one". Seasons not
# listed count every result. Used to work out when a title was settled.
_DROPPED_SCORE_SYSTEMS = [
    (range(1950, 1954), (0, 4)),
    (range(1954, 1958), (0, 5)),
    ((1958, 1960, 1963, 1964, 1965), (0, 6)),
    ((1959, 1961, 1962, 1966), (0, 5)),
    (range(1967, 1979), ("front", "all_but_one")),
    ((1979,), ("back", 4)),
    ((1980,), ("back", 5)),
    (range(1981, 1991), (0, 11)),
]


def dropped_score_rule(season: int) -> tuple | None:
    """(split, best) for a season whose championship dropped results, else None."""
    for seasons, rule in _DROPPED_SCORE_SYSTEMS:
        if season in seasons:
            return rule
    return None


def counted_points(points_by_round: dict[int, float], season: int, total_rounds: int) -> float:
    """A driver's championship points under the season's dropped-score rule:
    Jolpica's calculate_championship_points, for one driver."""
    rule = dropped_score_rule(season)
    if rule is None:
        return float(sum(points_by_round.values()))
    split, best = rule
    if split == 0:
        parts = [list(points_by_round.values())]
        sizes = [total_rounds]
    else:
        first = (total_rounds + 1) // 2 if split == "front" else total_rounds // 2
        parts = [[p for r, p in points_by_round.items() if r <= first],
                 [p for r, p in points_by_round.items() if r > first]]
        sizes = [first, total_rounds - first]
    total = 0.0
    for part, size in zip(parts, sizes):
        keep = size - 1 if best == "all_but_one" else best
        total += sum(sorted(part, reverse=True)[:keep])
    return total


def current_season() -> int:
    return datetime.now(timezone.utc).year


def available_seasons() -> list[int]:
    """The seasons the API serves, newest first: this year back to FIRST_SEASON."""
    return list(range(current_season(), FIRST_SEASON - 1, -1))


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
# Partial seasons add up, though: once a driver's part-time starts reach a
# full season's worth (this season's bar), they count as a season too, so a
# journeyman of three half-seasons isn't still a rookie in the fourth.
# Before ROOKIE_ANY_START_COUNTS_BEFORE, any championship start counts as a
# season: most Grand Prix careers then ran largely outside the championship
# (before it, and in non-championship races), and few regulars raced half
# its rounds, so Villoresi, a pre-war winner, isn't a 1951 rookie.
ROOKIE_ANY_START_COUNTS_BEFORE = 1960

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

# Season labels are relative to the season: the top SEASON_LABEL_SHARE of the
# graded field by net over/underperformance share are overperformers, the
# bottom as many underperformers (about the 14% / 13% the old fixed 0.3 bar
# averaged over 2003-2025). At least MIN_DRIVERS_PER_SEASON_LABEL each, so
# leave-one-out always has the class left to train on.
SEASON_LABEL_SHARE = 0.15
MIN_DRIVERS_PER_SEASON_LABEL = 2

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
# swing, as a share of what a Grand Prix win paid that season, when they come
# from the gainer winning or the rival retiring. 0.6 is 15 points at today's
# 25 for a win (a win against a rival's P5, or any retirement against a
# podium), and 5.4 when a win paid 9.
SEASON_SUMMARY_SWING_MIN_SHARE_OF_WIN = 0.6
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
