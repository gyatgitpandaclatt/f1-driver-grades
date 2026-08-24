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

export interface Meta {
  feature_importances: FeatureImportance[] | null;
  predicted_vs_actual: PredictedVsActualPoint[];
  misclassified: MisclassifiedEntry[];
  model_note: string | null;
  rf_metrics: RfMetrics | null;
  performance_label_distribution: Record<string, number>;
  total_race_entries: number;
}

export interface DriverGradesResponse {
  status: "ok";
  season: number;
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

// HTTP 503 — the upstream F1 provider is rate limiting us. Distinct from
// "error" because it is expected to clear on its own; `retry_after` is the
// provider's own Retry-After, in seconds.
export interface BusyResponse {
  status: "busy";
  retry_after: number;
  message: string;
}

export type DriverGradesApiResult =
  | DriverGradesResponse
  | NoDataResponse
  | BusyResponse
  | ErrorResponse;

// --- Race Summary ---
// Mirrors backend/app/race_summary/models.py field-for-field. Keep in sync.

export interface FinalClassificationEntry {
  position: number;
  driver_code: string;
  constructor: string;
  status: string;
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
  pit_stops: PitStop[];
  overtakes: Overtake[];
  battles: Battle[];
  // Lineup facts the data provider does not carry (e.g. a stand-in driver),
  // confirmed against this race's entry list before being handed to Claude.
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
  | ErrorResponse;
