from typing import List, Literal, Optional

from pydantic import BaseModel


class DriverGrade(BaseModel):
    driver_code: str
    driver_name: str
    constructor: str
    points: float
    position: int
    wins: int
    races: int
    is_rookie: bool
    season_label: str
    rf_pred_label: str
    lr_pred_label: str
    composite: float
    grade: str
    pts_score: float
    pos_score: float
    perf_score: float
    grid_score: float
    teammate_score: float
    qual_score: float
    qual_pos_score: float
    qual_pole_score: float
    qual_h2h_score: float
    tier_bonus: float
    label_bonus: float
    model_bonus: float
    rookie_bonus: float
    avg_finish_minus_grid: Optional[float]
    avg_qual_pos: Optional[float]
    pole_rate: Optional[float]
    overperf_share: float
    underperf_share: float
    qual_h2h_wins: int
    qual_h2h_races: int


class FeatureImportance(BaseModel):
    feature: str
    importance: float


class PredictedVsActualPoint(BaseModel):
    driver_code: str
    actual_label: str
    predicted_label: str
    correct: bool


class MisclassifiedEntry(BaseModel):
    driver_code: str
    actual_label: str
    predicted_label: str


class Meta(BaseModel):
    feature_importances: Optional[List[FeatureImportance]]
    predicted_vs_actual: List[PredictedVsActualPoint]
    misclassified: List[MisclassifiedEntry]
    model_note: Optional[str]
    performance_label_distribution: dict[str, int]
    total_race_entries: int


class DriverGradesResponse(BaseModel):
    status: Literal["ok"]
    season: int
    current_round: int
    last_updated: str
    drivers: List[DriverGrade]
    meta: Meta


class NoDataResponse(BaseModel):
    status: Literal["no_data"]
    season: int
    message: str


class ErrorResponse(BaseModel):
    status: Literal["error"]
    message: str
