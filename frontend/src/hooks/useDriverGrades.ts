import { useCallback, useEffect, useRef, useState } from "react";
import { fetchDriverGrades, refreshDriverGrades } from "../api/client";
import { useAutoRetry } from "./useAutoRetry";
import type { DriverGrade, Meta } from "../api/types";

export type UIStatus = "loading" | "ok" | "error" | "no_data" | "busy";

interface State {
  status: UIStatus;
  drivers: DriverGrade[];
  meta: Meta | null;
  season: number | null;
  currentRound: number | null;
  lastUpdated: string | null;
  message: string | null;
}

const initialState: State = {
  status: "loading",
  drivers: [],
  meta: null,
  season: null,
  currentRound: null,
  lastUpdated: null,
  message: null,
};

const UNREACHABLE_MESSAGE =
  "Could not reach the backend. Is it running at the configured API URL?";

export function useDriverGrades() {
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
      const result = await fetchDriverGrades();
      if (result.status === "busy") {
        setState((s) => ({ ...s, status: "busy", message: result.message }));
        schedule(result.retry_after);
        return;
      }
      if (result.status === "ok") {
        setState({
          status: "ok",
          drivers: result.drivers,
          meta: result.meta,
          season: result.season,
          currentRound: result.current_round,
          lastUpdated: result.last_updated,
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
      const result = await refreshDriverGrades();
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
          drivers: result.drivers,
          meta: result.meta,
          season: result.season,
          currentRound: result.current_round,
          lastUpdated: result.last_updated,
          message: null,
        });
      } else if (state.status !== "ok") {
        // Not yet showing real data — safe to switch the whole view to
        // reflect the new no_data/error state.
        setState((s) => ({ ...s, status: result.status, message: result.message }));
      } else {
        // Already showing good data — a failed refresh shouldn't blank the
        // page, just surface an inline error near the refresh button.
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
