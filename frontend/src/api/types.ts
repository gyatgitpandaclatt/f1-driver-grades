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

export interface Meta {
  feature_importances: FeatureImportance[] | null;
  predicted_vs_actual: PredictedVsActualPoint[];
  misclassified: MisclassifiedEntry[];
  model_note: string | null;
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
