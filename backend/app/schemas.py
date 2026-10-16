from typing import List, Literal, Optional

from pydantic import BaseModel


class DriverGrade(BaseModel):
    driver_code: str
    driver_name: str
    constructor: str
    points: float
    position: int
    # How the championship listed them: the position, or "-" (not
    # classified), "D" (disqualified) or "E" (excluded).
    position_text: str = ""
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


class RfClassMetrics(BaseModel):
    label: str
    precision: float
    recall: float
    f1: float
    support: int


class RfMetrics(BaseModel):
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    per_class: List[RfClassMetrics]


class QualH2HPair(BaseModel):
    constructor: str
    driver_a: str
    driver_b: str
    a_wins: int
    b_wins: int
    races: int


class ExcludedDriver(BaseModel):
    driver_code: str
    driver_name: str
    races: int


class ConstructorTier(BaseModel):
    constructor: str
    position: int
    points: float
    tier: float
    tier_bonus: float


class Meta(BaseModel):
    feature_importances: Optional[List[FeatureImportance]]
    predicted_vs_actual: List[PredictedVsActualPoint]
    misclassified: List[MisclassifiedEntry]
    model_note: Optional[str]
    rf_metrics: Optional[RfMetrics]
    performance_label_distribution: dict[str, int]
    total_race_entries: int
    # None until anyone clears the bar (after round 1 nobody has two races),
    # when nobody is left out.
    min_races_for_grade: Optional[int]
    qual_h2h_pairs: List[QualH2HPair]
    # Drivers below that bar (stand-ins, part-timers), left out of the grades.
    excluded_drivers: List[ExcludedDriver]
    # Full prior seasons below which a driver counts as a rookie.
    rookie_season_threshold: int
    # This season's constructors' championship order and the tiers set from it.
    constructor_tiers: List[ConstructorTier]
    # Rounds without qualifying data (every round before the mid-1990s),
    # where the starting grid stood in for the qualifying order.
    grid_as_qualifying_rounds: List[int] = []
    # "standings": the constructors' championship. "results": the
    # constructors' points in the race results, for the seasons before the
    # championship began in 1958.
    constructor_tiers_source: Literal["standings", "results"] = "standings"
    # Constructors that ran five or more cars in a Grand Prix: a make raced
    # by privateers too, whose drivers may not all be teammates.
    makes_with_privateers: List[str] = []
    # Only a driver's best results counted (to 1990): points are counted points.
    dropped_scores: bool = False


class DriverGradesResponse(BaseModel):
    status: Literal["ok"]
    season: int
    # False for a finished season, whose figures are final.
    is_current_season: bool
    current_round: int
    last_updated: str
    drivers: List[DriverGrade]
    meta: Meta
    # Served from a saved snapshot of a finished season (see snapshots.py).
    snapshot: bool = False


class SeasonsResponse(BaseModel):
    current: int
    # Newest first, the current season included.
    seasons: List[int]


class NoDataResponse(BaseModel):
    status: Literal["no_data"]
    season: int
    message: str


class ErrorResponse(BaseModel):
    status: Literal["error"]
    message: str
