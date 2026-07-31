import { useCallback, useEffect, useState } from "react";
import { fetchRaceSummary, refreshRaceSummary } from "../api/client";
import type { RaceSummaryChartData, RaceSummaryContext, RaceSummarySections } from "../api/types";

export type UIStatus = "loading" | "ok" | "error" | "no_data";

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

  const load = useCallback(async () => {
    setState((s) => ({ ...s, status: "loading" }));
    try {
      const result = await fetchRaceSummary();
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
  }, []);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    setRefreshError(null);
    try {
      const result = await refreshRaceSummary();
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
  }, [state.status]);

  useEffect(() => {
    load();
  }, [load]);

  return { ...state, refresh, refreshing, refreshError };
}
