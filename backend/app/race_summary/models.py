from typing import Dict, List, Literal, Optional

from pydantic import BaseModel


class FinalClassificationEntry(BaseModel):
    position: int
    driver_code: str


class OvertakeOut(BaseModel):
    lap: int
    overtaking_driver: str
    overtaken_driver: str
    track_status: str


class PitStopOut(BaseModel):
    driver: str
    lap_number: int
    compound: Optional[str]
    duration_seconds: Optional[float]
    tyre_life: Optional[float]


class StintOut(BaseModel):
    driver: str
    compound: str
    lap_start: int
    lap_end: int


class BattleOut(BaseModel):
    driver1: str
    driver2: str
    close_laps: int


class SafetyCarEventOut(BaseModel):
    time: str
    message: str
    lap: Optional[int] = None


class TelemetryHighlightOut(BaseModel):
    driver: str
    max_speed_kph: Optional[float]
    top_speed_lap: Optional[int]


class RaceSummarySections(BaseModel):
    summary: str
    lap_highlights: str
    pit_analysis: str
    overtakes_battles: str
    telemetry_spotlight: str
    driver_of_the_day: str


class SpeedTracePoint(BaseModel):
    distance: float
    speed: float


class RaceSummaryChartData(BaseModel):
    # Each row is {"lap": N, "<driver_code>": position, ...} — shaped for a
    # Recharts multi-line chart with one Line per driver.
    position_series: List[Dict[str, float]]
    speed_traces: Dict[str, List[SpeedTracePoint]]


class RaceSummaryContext(BaseModel):
    race_name: str
    year: int
    round: int
    total_laps: int
    weather_summary: str
    final_classification: List[FinalClassificationEntry]
    pit_stops: List[PitStopOut]
    overtakes: List[OvertakeOut]
    key_events: List[SafetyCarEventOut]
    strategies: List[StintOut]
    battles: List[BattleOut]
    telemetry_highlights: List[TelemetryHighlightOut]


class RaceSummaryResponse(BaseModel):
    status: Literal["ok"]
    season: int
    round: int
    race_name: str
    last_updated: str
    sections: RaceSummarySections
    context: RaceSummaryContext
    charts: RaceSummaryChartData
