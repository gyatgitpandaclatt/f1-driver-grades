from typing import Dict, List, Literal, Optional

from pydantic import BaseModel


class StandingEntry(BaseModel):
    position: int
    driver_code: str
    driver_name: str
    constructor: str  # the one they raced for most
    points: float
    wins: int
    podiums: int
    dnfs: int
    races: int
    # Raced too little to count as a full-season driver (the grades' bar).
    part_time: bool


class ConstructorStanding(BaseModel):
    position: int
    constructor: str
    points: float
    wins: int


class RaceResultOut(BaseModel):
    round: int
    race_name: str
    winner: str
    podium: List[str]


class DriverPoints(BaseModel):
    driver_code: str
    points: float


class DriverWins(BaseModel):
    driver_code: str
    wins: int


class QuarterOut(BaseModel):
    label: str  # "Q1".."Q4"
    first_round: int
    last_round: int
    first_race: str
    last_race: str
    leader_at_start: Optional[str]  # None for Q1: no table before round 1
    leader: str
    leader_points: float
    runner_up: Optional[str]
    margin: Optional[float]  # leader's lead over the runner-up at quarter end
    lead_changes: int
    top_scorers: List[DriverPoints]  # points scored within the quarter
    winners: List[DriverWins]


class MomentOut(BaseModel):
    round: int
    race_name: str
    # title_decided, lead_change, points_swing, contender_duel; first_win,
    # win_outside_top, first_podium, rookie_first_points, crucial_points
    kinds: List[str]
    headline: str  # built from the data, not by the narrator
    drivers: List[str]


class StintOut(BaseModel):
    constructor: str
    rounds: List[int]


class PartTimeDriverOut(BaseModel):
    driver_code: str
    driver_name: str
    races: int
    points: float
    best_finish: Optional[int]
    stints: List[StintOut]
    # Drivers the team started the season with who were out of the car
    # while this driver was in it.
    in_place_of: List[str]
    highlights: List[str]  # career firsts this season held
    summary: str


class LineupChangeOut(BaseModel):
    round: int
    race_name: str
    constructor: str
    driver_in: Optional[str]
    driver_out: Optional[str]


class TitleDecidedOut(BaseModel):
    round: int
    race_name: str
    driver_code: str
    rounds_left: int


class ChampionOut(BaseModel):
    driver_code: str
    driver_name: str
    constructor: str
    points: float


class SeasonSummarySections(BaseModel):
    summary: str
    championship_progression: str
    quarterly_analysis: str
    championship_moments: str
    other_moments: str
    driver_of_the_season: str


class RoundLabel(BaseModel):
    round: int
    race_name: str


class SeasonSummaryChartData(BaseModel):
    # Each row is {"round": N, "<driver_code>": championship position, ...},
    # the same shape as the race summary's lap chart.
    standings_series: List[Dict[str, float]]
    rounds: List[RoundLabel]
    highlight_drivers: List[str]


class SeasonSummaryContext(BaseModel):
    season: int
    rounds: int
    final_standings: List[StandingEntry]
    constructor_standings: List[ConstructorStanding]
    races: List[RaceResultOut]
    quarters: List[QuarterOut]
    title_decided: TitleDecidedOut
    championship_moments: List[MomentOut]
    other_moments: List[MomentOut]
    part_time_drivers: List[PartTimeDriverOut]
    lineup_changes: List[LineupChangeOut]
    rookies: List[str]


class SeasonSummaryResponse(BaseModel):
    status: Literal["ok"]
    season: int
    rounds: int
    champion: ChampionOut
    last_updated: str
    sections: SeasonSummarySections
    context: SeasonSummaryContext
    charts: SeasonSummaryChartData
    # Served from a saved snapshot (see snapshots.py): refreshing can't change it.
    snapshot: bool = False
