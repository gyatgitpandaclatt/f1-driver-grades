import type { DriverGradesApiResult, RaceSummaryApiResult } from "./types";

// Relative paths: in dev, Vite's server.proxy forwards /api to the backend
// (see vite.config.ts); in production, FastAPI serves the built frontend
// and the API from the same origin (see backend/app/main.py).

async function parseResult<T>(res: Response): Promise<T> {
  // The backend always returns a JSON body with a `status` field, even on
  // 502/500 (see main.py exception handlers), so we can parse regardless
  // of res.ok.
  return (await res.json()) as T;
}

export async function fetchDriverGrades(): Promise<DriverGradesApiResult> {
  const res = await fetch("/api/driver-grades");
  return parseResult<DriverGradesApiResult>(res);
}

export async function refreshDriverGrades(): Promise<DriverGradesApiResult> {
  const res = await fetch("/api/refresh", { method: "POST" });
  return parseResult<DriverGradesApiResult>(res);
}

export async function fetchRaceSummary(): Promise<RaceSummaryApiResult> {
  const res = await fetch("/api/race-summary");
  return parseResult<RaceSummaryApiResult>(res);
}

export async function refreshRaceSummary(): Promise<RaceSummaryApiResult> {
  const res = await fetch("/api/race-summary/refresh", { method: "POST" });
  return parseResult<RaceSummaryApiResult>(res);
}
