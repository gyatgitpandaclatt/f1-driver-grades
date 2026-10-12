// Mirrors backend/app/schemas.py field-for-field. Keep in sync.

export interface DriverGrade {
  driver_code: string;
  driver_name: string;
  constructor: string;
  points: number;
  position: number;
  wins: number;
  races: number;
  is_rookie: boolean;
  season_label: string;
  rf_pred_label: string;
  lr_pred_label: string;
  composite: number;
  grade: string;
  pts_score: number;
  pos_score: number;
  perf_score: number;
  grid_score: number;
  teammate_score: number;
  qual_score: number;
  qual_pos_score: number;
  qual_pole_score: number;
  qual_h2h_score: number;
  tier_bonus: number;
  label_bonus: number;
  model_bonus: number;
  rookie_bonus: number;
  avg_finish_minus_grid: number | null;
  avg_qual_pos: number | null;
  pole_rate: number | null;
  overperf_share: number;
  underperf_share: number;
  qual_h2h_wins: number;
  qual_h2h_races: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface PredictedVsActualPoint {
  driver_code: string;
  actual_label: string;
  predicted_label: string;
  correct: boolean;
}

export interface MisclassifiedEntry {
  driver_code: string;
  actual_label: string;
  predicted_label: string;
}

export interface RfClassMetrics {
  label: string;
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

export interface RfMetrics {
  accuracy: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
  per_class: RfClassMetrics[];
}

// Teammate qualifying head-to-head, counted only over the rounds the two
// shared a car.
export interface QualH2HPair {
  constructor: string;
  driver_a: string;
  driver_b: string;
  a_wins: number;
  b_wins: number;
  races: number;
}

// A driver below the race-count bar (a stand-in, a part-timer), left out of
// the grades.
export interface ExcludedDriver {
  driver_code: string;
  driver_name: string;
  races: number;
}

// A constructor's place in that season's constructors' championship, and the
// car tier and tier bonus set from it.
export interface ConstructorTier {
  constructor: string;
  position: number;
  points: number;
  tier: number;
  tier_bonus: number;
}

export interface Meta {
  feature_importances: FeatureImportance[] | null;
  predicted_vs_actual: PredictedVsActualPoint[];
  misclassified: MisclassifiedEntry[];
  model_note: string | null;
  rf_metrics: RfMetrics | null;
  performance_label_distribution: Record<string, number>;
  total_race_entries: number;
  // null until anyone clears the bar, when nobody is left out.
  min_races_for_grade: number | null;
  qual_h2h_pairs: QualH2HPair[];
  excluded_drivers: ExcludedDriver[];
  // Full prior seasons below which a driver counts as a rookie.
  rookie_season_threshold: number;
  constructor_tiers: ConstructorTier[];
}

export interface DriverGradesResponse {
  status: "ok";
  season: number;
  // False for a finished season, whose figures are final.
  is_current_season: boolean;
  current_round: number;
  last_updated: string;
  drivers: DriverGrade[];
  meta: Meta;
}

export interface NoDataResponse {
  status: "no_data";
  season: number;
  message: string;
}

export interface ErrorResponse {
  status: "error";
  message: string;
}

// HTTP 503 with status "unavailable" — the narrative cannot be generated for
// a reason retrying will not fix (credit balance, rejected key). Distinct from
// "busy", which clears on its own.
export interface UnavailableResponse {
  status: "unavailable";
  message: string;
}

// HTTP 503 — the upstream F1 provider is rate limiting us. Distinct from
// "error" because it is expected to clear on its own; `retry_after` is the
// provider's own Retry-After, in seconds.
export interface BusyResponse {
  status: "busy";
  retry_after: number;
  message: string;
}

export interface SeasonsResponse {
  current: number;
  // Newest first, the current season included.
  seasons: number[];
}

export type SeasonsApiResult = SeasonsResponse | ErrorResponse;

export type DriverGradesApiResult =
  | DriverGradesResponse
  | NoDataResponse
  | BusyResponse
  | UnavailableResponse
  | ErrorResponse;

// --- Race Summary ---
// Mirrors backend/app/race_summary/models.py field-for-field. Keep in sync.

export interface FinalClassificationEntry {
  position: number;
  driver_code: string;
  constructor: string;
  status: string;
}

export interface Retirement {
  driver_code: string;
  constructor: string;
  status: string;
  laps_completed: number;
}

export interface Overtake {
  lap: number;
  overtaking_driver: string;
  overtaken_driver: string;
}

export interface PitStop {
  driver: string;
  lap_number: number;
  stop_number: number;
  duration_seconds: number | null;
}

export interface Battle {
  driver1: string;
  driver2: string;
  close_laps: number;
}

export interface RaceSummarySections {
  summary: string;
  lap_highlights: string;
  pit_analysis: string;
  overtakes_battles: string;
  driver_of_the_day: string;
}

export interface RaceSummaryChartData {
  // Each row is {lap: N, <driver_code>: position, ...}
  position_series: Record<string, number>[];
}

export interface RaceSummaryContext {
  race_name: string;
  year: number;
  round: number;
  total_laps: number;
  final_classification: FinalClassificationEntry[];
  retirements: Retirement[];
  pit_stops: PitStop[];
  overtakes: Overtake[];
  battles: Battle[];
  // Lineup facts the data provider does not carry (e.g. a stand-in driver),
  // confirmed against this race's entry list before being handed to the narrative model.
  lineup_notes: string[];
}

export interface RaceSummaryResponse {
  status: "ok";
  season: number;
  round: number;
  race_name: string;
  last_updated: string;
  sections: RaceSummarySections;
  context: RaceSummaryContext;
  charts: RaceSummaryChartData;
}

export type RaceSummaryApiResult =
  | RaceSummaryResponse
  | NoDataResponse
  | BusyResponse
  | UnavailableResponse
  | ErrorResponse;

// --- Season Summary ---
// Mirrors backend/app/season_summary/models.py field-for-field. Keep in sync.

export interface StandingEntry {
  position: number;
  driver_code: string;
  driver_name: string;
  constructor: string;
  points: number;
  wins: number;
  podiums: number;
  dnfs: number;
  races: number;
  part_time: boolean;
}

export interface ConstructorStanding {
  position: number;
  constructor: string;
  points: number;
  wins: number;
}

export interface RaceResultSummary {
  round: number;
  race_name: string;
  winner: string;
  podium: string[];
}

export interface DriverPoints {
  driver_code: string;
  points: number;
}

export interface DriverWins {
  driver_code: string;
  wins: number;
}

export interface Quarter {
  label: string;
  first_round: number;
  last_round: number;
  first_race: string;
  last_race: string;
  leader_at_start: string | null;
  leader: string;
  leader_points: number;
  runner_up: string | null;
  margin: number | null;
  lead_changes: number;
  top_scorers: DriverPoints[];
  winners: DriverWins[];
}

export interface Moment {
  round: number;
  race_name: string;
  kinds: string[];
  // Built from the data by the backend, not by the narrative model.
  headline: string;
  drivers: string[];
}

export interface Stint {
  constructor: string;
  rounds: number[];
}

export interface PartTimeDriver {
  driver_code: string;
  driver_name: string;
  races: number;
  points: number;
  best_finish: number | null;
  stints: Stint[];
  in_place_of: string[];
  highlights: string[];
  summary: string;
}

export interface LineupChange {
  round: number;
  race_name: string;
  constructor: string;
  driver_in: string | null;
  driver_out: string | null;
}

export interface TitleDecided {
  round: number;
  race_name: string;
  driver_code: string;
  rounds_left: number;
}

export interface Champion {
  driver_code: string;
  driver_name: string;
  constructor: string;
  points: number;
}

export interface SeasonSummarySections {
  summary: string;
  championship_progression: string;
  quarterly_analysis: string;
  championship_moments: string;
  other_moments: string;
  driver_of_the_season: string;
}

export interface RoundLabel {
  round: number;
  race_name: string;
}

export interface SeasonSummaryChartData {
  // Each row is {round: N, <driver_code>: championship position, ...}
  standings_series: Record<string, number>[];
  rounds: RoundLabel[];
  highlight_drivers: string[];
}

export interface SeasonSummaryContext {
  season: number;
  rounds: number;
  final_standings: StandingEntry[];
  constructor_standings: ConstructorStanding[];
  races: RaceResultSummary[];
  quarters: Quarter[];
  title_decided: TitleDecided;
  championship_moments: Moment[];
  other_moments: Moment[];
  part_time_drivers: PartTimeDriver[];
  lineup_changes: LineupChange[];
  rookies: string[];
}

export interface SeasonSummaryResponse {
  status: "ok";
  season: number;
  rounds: number;
  champion: Champion;
  last_updated: string;
  sections: SeasonSummarySections;
  context: SeasonSummaryContext;
  charts: SeasonSummaryChartData;
}

export type SeasonSummaryApiResult =
  | SeasonSummaryResponse
  | NoDataResponse
  | BusyResponse
  | UnavailableResponse
  | ErrorResponse;
