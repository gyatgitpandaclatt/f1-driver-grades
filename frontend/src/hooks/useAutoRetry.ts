import { useCallback, useEffect, useRef } from "react";

/**
 * The backend answers 503 + Retry-After when the upstream F1 provider rate
 * limits it (see main.py's UpstreamRateLimitedError handler). That clears on
 * its own, so wait out the provider's own delay and reload rather than making
 * the visitor press Retry on something that is merely busy.
 */
export function useAutoRetry(load: () => void) {
  const timer = useRef<number | null>(null);
  const mounted = useRef(true);

  const cancel = useCallback(() => {
    if (timer.current !== null) {
      window.clearTimeout(timer.current);
      timer.current = null;
    }
  }, []);

  const schedule = useCallback(
    (retryAfterSeconds: number) => {
      // A request in flight at unmount still resolves, and a "busy" result
      // calls back in here. Without this guard it would arm a timer nothing
      // cleans up, reloading data for a page that is gone.
      if (!mounted.current) return;
      cancel();
      timer.current = window.setTimeout(() => {
        timer.current = null;
        load();
      }, Math.max(1, retryAfterSeconds) * 1000);
    },
    [cancel, load],
  );

  useEffect(() => {
    // Set on every run, not just the first: StrictMode mounts, cleans up,
    // and mounts again in dev, and a flag only ever set to false would
    // leave auto-retry dead for the rest of the session.
    mounted.current = true;
    return () => {
      mounted.current = false;
      cancel();
    };
  }, [cancel]);

  return { schedule, cancel };
}
