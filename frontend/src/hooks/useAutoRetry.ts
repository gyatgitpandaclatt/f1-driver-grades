import { useCallback, useEffect, useRef } from "react";

/**
 * The backend answers 503 + Retry-After when the upstream F1 provider rate
 * limits it (see main.py's UpstreamRateLimitedError handler). That clears on
 * its own, so wait out the provider's own delay and reload rather than making
 * the visitor press Retry on something that is merely busy.
 */
export function useAutoRetry(load: () => void) {
  const timer = useRef<number | null>(null);

  const cancel = useCallback(() => {
    if (timer.current !== null) {
      window.clearTimeout(timer.current);
      timer.current = null;
    }
  }, []);

  const schedule = useCallback(
    (retryAfterSeconds: number) => {
      cancel();
      timer.current = window.setTimeout(() => {
        timer.current = null;
        load();
      }, Math.max(1, retryAfterSeconds) * 1000);
    },
    [cancel, load],
  );

  useEffect(() => cancel, [cancel]);

  return { schedule, cancel };
}
