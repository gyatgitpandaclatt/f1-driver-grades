// Mirrors backend/app/schemas.py field-for-field. Keep in sync.

export interface HealthResponse {
  status: "ok";
  race_summary_available: boolean;
}

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

export type DriverGradesApiResult = DriverGradesResponse | NoDataResponse | ErrorResponse;

// --- Race Summary ---
// Mirrors backend/app/race_summary/models.py field-for-field. Keep in sync.

export interface FinalClassificationEntry {
  position: number;
  driver_code: string;
}

export interface Overtake {
  lap: number;
  overtaking_driver: string;
  overtaken_driver: string;
  track_status: string;
}

export interface PitStop {
  driver: string;
  lap_number: number;
  compound: string | null;
  duration_seconds: number | null;
  tyre_life: number | null;
}

export interface Stint {
  driver: string;
  compound: string;
  lap_start: number;
  lap_end: number;
}

export interface Battle {
  driver1: string;
  driver2: string;
  close_laps: number;
}

export interface SafetyCarEvent {
  time: string;
  message: string;
  lap: number | null;
}

export interface TelemetryHighlight {
  driver: string;
  max_speed_kph: number | null;
  top_speed_lap: number | null;
}

export interface RaceSummarySections {
  summary: string;
  lap_highlights: string;
  pit_analysis: string;
  overtakes_battles: string;
  telemetry_spotlight: string;
  driver_of_the_day: string;
}

export interface SpeedTracePoint {
  distance: number;
  speed: number;
}

export interface RaceSummaryChartData {
  // Each row is {lap: N, <driver_code>: position, ...}
  position_series: Record<string, number>[];
  speed_traces: Record<string, SpeedTracePoint[]>;
}

export interface RaceSummaryContext {
  race_name: string;
  year: number;
  round: number;
  total_laps: number;
  weather_summary: string;
  final_classification: FinalClassificationEntry[];
  pit_stops: PitStop[];
  overtakes: Overtake[];
  key_events: SafetyCarEvent[];
  strategies: Stint[];
  battles: Battle[];
  telemetry_highlights: TelemetryHighlight[];
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

export type RaceSummaryApiResult = RaceSummaryResponse | NoDataResponse | ErrorResponse;
