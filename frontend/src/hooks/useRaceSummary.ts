import { useCallback, useEffect, useRef, useState } from "react";
import { fetchRaceSummary, refreshRaceSummary } from "../api/client";
import { useAutoRetry } from "./useAutoRetry";
import type { RaceSummaryChartData, RaceSummaryContext, RaceSummarySections } from "../api/types";

export type UIStatus = "loading" | "ok" | "error" | "no_data" | "busy";

interface State {
  status: UIStatus;
  season: number | null;
  round: number | null;
  raceName: string | null;
  lastUpdated: string | null;
  sections: RaceSummarySections | null;
  context: RaceSummaryContext | null;
  charts: RaceSummaryChartData | null;
  message: string | null;
}

const initialState: State = {
  status: "loading",
  season: null,
  round: null,
  raceName: null,
  lastUpdated: null,
  sections: null,
  context: null,
  charts: null,
  message: null,
};

const UNREACHABLE_MESSAGE =
  "Could not reach the backend. Is it running at the configured API URL?";

export function useRaceSummary() {
  const [state, setState] = useState<State>(initialState);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const loadRef = useRef<(() => void) | null>(null);
  const { schedule, cancel } = useAutoRetry(loadRef);

  const load = useCallback(async () => {
    // Supersede any retry already scheduled: without this, a timer armed by
    // an earlier "busy" response fires after this load succeeds and throws
    // the page back to a loading state over data that is already good.
    cancel();
    setState((s) => ({ ...s, status: "loading" }));
    try {
      const result = await fetchRaceSummary();
      if (result.status === "busy") {
        setState((s) => ({ ...s, status: "busy", message: result.message }));
        schedule(result.retry_after);
        return;
      }
      if (result.status === "ok") {
        setState({
          status: "ok",
          season: result.season,
          round: result.round,
          raceName: result.race_name,
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
      setState((s) => ({ ...s, status: "error", message: UNREACHABLE_MESSAGE }));
    }
  }, [cancel, schedule]);

  const refresh = useCallback(async () => {
    cancel();
    setRefreshing(true);
    setRefreshError(null);
    try {
      const result = await refreshRaceSummary();
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
          round: result.round,
          raceName: result.race_name,
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
      if (state.status !== "ok") {
        setState((s) => ({ ...s, status: "error", message: UNREACHABLE_MESSAGE }));
      } else {
        setRefreshError(UNREACHABLE_MESSAGE);
      }
    } finally {
      setRefreshing(false);
    }
  }, [state.status, cancel, schedule]);

  useEffect(() => {
    loadRef.current = load;
  }, [load]);

  useEffect(() => {
    load();
    return cancel;
  }, [load, cancel]);

  return { ...state, refresh, refreshing, refreshError };
}
