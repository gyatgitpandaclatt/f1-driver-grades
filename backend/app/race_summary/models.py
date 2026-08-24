from typing import Dict, List, Literal, Optional

from pydantic import BaseModel


class FinalClassificationEntry(BaseModel):
    position: int
    driver_code: str
    constructor: str
    status: str  # "Finished", "+1 Lap", "Retired", "Accident", "Engine", ...


class RetirementOut(BaseModel):
    driver_code: str
    constructor: str
    status: str  # cause as recorded by the results feed: "Collision", "Engine", ...
    laps_completed: int


class OvertakeOut(BaseModel):
    lap: int
    overtaking_driver: str
    overtaken_driver: str


class PitStopOut(BaseModel):
    driver: str
    lap_number: int
    stop_number: int
    duration_seconds: Optional[float]


class BattleOut(BaseModel):
    driver1: str
    driver2: str
    close_laps: int


class RaceSummarySections(BaseModel):
    summary: str
    lap_highlights: str
    pit_analysis: str
    overtakes_battles: str
    driver_of_the_day: str


class RaceSummaryChartData(BaseModel):
    # Each row is {"lap": N, "<driver_code>": position, ...} — shaped for a
    # Recharts multi-line chart with one Line per driver.
    position_series: List[Dict[str, float]]


class RaceSummaryContext(BaseModel):
    race_name: str
    year: int
    round: int
    total_laps: int
    final_classification: List[FinalClassificationEntry]
    # Everyone who did not go the distance. Absent from final_classification,
    # which by definition only holds classified runners.
    retirements: List[RetirementOut] = []
    pit_stops: List[PitStopOut]
    overtakes: List[OvertakeOut]
    battles: List[BattleOut]
    # Lineup facts the provider does not carry (e.g. a stand-in driver),
    # supplied from config and confirmed against this race's classification.
    lineup_notes: List[str] = []


class RaceSummaryResponse(BaseModel):
    status: Literal["ok"]
    season: int
    round: int
    race_name: str
    last_updated: str
    sections: RaceSummarySections
    context: RaceSummaryContext
    charts: RaceSummaryChartData
