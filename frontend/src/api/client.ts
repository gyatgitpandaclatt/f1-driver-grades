import type {
  DriverGradesApiResult,
  RaceSummaryApiResult,
  SeasonsApiResult,
  SeasonSummaryApiResult,
} from "./types";

// Relative paths: in dev, Vite's server.proxy forwards /api to the backend
// (see vite.config.ts); in production, FastAPI serves the built frontend
// and the API from the same origin (see backend/app/main.py).

async function parseResult<T>(res: Response): Promise<T> {
  // The backend always returns a JSON body with a `status` field, even on
  // 502/503/500 (see main.py exception handlers), so we can parse regardless
  // of res.ok — but something between us and it may not. A proxy that cuts a
  // slow request, or a gateway error page, returns HTML, and res.json() then
  // throws, which the hooks could only report as the misleading "could not
  // reach the backend". Fall back to a real error result instead.
  const body = await res.text();
  try {
    return JSON.parse(body) as T;
  } catch {
    const message = res.ok
      ? "The server sent a response we could not read. Please try again."
      : `The server returned an error (HTTP ${res.status}). Please try again shortly.`;
    return { status: "error", message } as T;
  }
}

// null asks for the current season, the backend's default.
function seasonQuery(season: number | null): string {
  return season == null ? "" : `?season=${season}`;
}

export async function fetchSeasons(): Promise<SeasonsApiResult> {
  const res = await fetch("/api/seasons");
  return parseResult<SeasonsApiResult>(res);
}

export async function fetchDriverGrades(season: number | null): Promise<DriverGradesApiResult> {
  const res = await fetch(`/api/driver-grades${seasonQuery(season)}`);
  return parseResult<DriverGradesApiResult>(res);
}

export async function refreshDriverGrades(season: number | null): Promise<DriverGradesApiResult> {
  const res = await fetch(`/api/refresh${seasonQuery(season)}`, { method: "POST" });
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

export async function fetchSeasonSummary(season: number): Promise<SeasonSummaryApiResult> {
  const res = await fetch(`/api/season-summary${seasonQuery(season)}`);
  return parseResult<SeasonSummaryApiResult>(res);
}

export async function refreshSeasonSummary(season: number): Promise<SeasonSummaryApiResult> {
  const res = await fetch(`/api/season-summary/refresh${seasonQuery(season)}`, { method: "POST" });
  return parseResult<SeasonSummaryApiResult>(res);
}
