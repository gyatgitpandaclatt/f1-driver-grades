import { useCallback, useEffect, useRef, useState } from "react";
import { fetchSeasonSummary, refreshSeasonSummary } from "../api/client";
import { useAutoRetry } from "./useAutoRetry";
import type {
  Champion,
  SeasonSummaryChartData,
  SeasonSummaryContext,
  SeasonSummarySections,
} from "../api/types";

export type UIStatus = "loading" | "ok" | "error" | "no_data" | "busy" | "unavailable";

interface State {
  status: UIStatus;
  season: number | null;
  rounds: number | null;
  champion: Champion | null;
  lastUpdated: string | null;
  sections: SeasonSummarySections | null;
  context: SeasonSummaryContext | null;
  charts: SeasonSummaryChartData | null;
  message: string | null;
}

const initialState: State = {
  status: "loading",
  season: null,
  rounds: null,
  champion: null,
  lastUpdated: null,
  sections: null,
  context: null,
  charts: null,
  message: null,
};

const UNREACHABLE_MESSAGE =
  "Could not reach the backend. Is it running at the configured API URL?";

export function useSeasonSummary(season: number) {
  const [state, setState] = useState<State>(initialState);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const loadRef = useRef<(() => void) | null>(null);
  const { schedule, cancel } = useAutoRetry(loadRef);
  // Only the latest request may land (see useDriverGrades).
  const latestRequest = useRef(0);

  const load = useCallback(async () => {
    // Supersede any retry already scheduled: without this, a timer armed by
    // an earlier "busy" response fires after this load succeeds and throws
    // the page back to a loading state over data that is already good.
    cancel();
    const request = ++latestRequest.current;
    setState((s) => ({ ...s, status: "loading" }));
    try {
      const result = await fetchSeasonSummary(season);
      if (request !== latestRequest.current) return;
      if (result.status === "busy") {
        setState((s) => ({ ...s, status: "busy", message: result.message }));
        schedule(result.retry_after);
        return;
      }
      if (result.status === "ok") {
        setState({
          status: "ok",
          season: result.season,
          rounds: result.rounds,
          champion: result.champion,
          lastUpdated: result.last_updated,
          sections: result.sections,
          context: result.context,
          charts: result.charts,
          message: null,
        });
      } else {
        setState((s) => ({ ...s, status: result.status, message: result.message }));
      }
    } catch {
      if (request !== latestRequest.current) return;
      setState((s) => ({ ...s, status: "error", message: UNREACHABLE_MESSAGE }));
    }
  }, [cancel, schedule, season]);

  const refresh = useCallback(async () => {
    cancel();
    const request = ++latestRequest.current;
    setRefreshing(true);
    setRefreshError(null);
    try {
      const result = await refreshSeasonSummary(season);
      if (request !== latestRequest.current) return;
      if (result.status === "busy") {
        if (state.status !== "ok") {
          setState((s) => ({ ...s, status: "busy", message: result.message }));
        } else {
          setRefreshError(result.message);
        }
        schedule(result.retry_after);
        return;
      }
      if (result.status === "ok") {
        setState({
          status: "ok",
          season: result.season,
          rounds: result.rounds,
          champion: result.champion,
          lastUpdated: result.last_updated,
          sections: result.sections,
          context: result.context,
          charts: result.charts,
          message: null,
        });
      } else if (state.status !== "ok") {
        setState((s) => ({ ...s, status: result.status, message: result.message }));
      } else {
        setRefreshError(result.message);
      }
    } catch {
      if (request !== latestRequest.current) return;
      if (state.status !== "ok") {
        setState((s) => ({ ...s, status: "error", message: UNREACHABLE_MESSAGE }));
      } else {
        setRefreshError(UNREACHABLE_MESSAGE);
      }
    } finally {
      setRefreshing(false);
    }
  }, [state.status, cancel, schedule, season]);

  useEffect(() => {
    loadRef.current = load;
  }, [load]);

  useEffect(() => {
    load();
    return cancel;
  }, [load, cancel]);

  return { ...state, refresh, refreshing, refreshError };
}
