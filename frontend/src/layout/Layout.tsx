import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { fetchHealth } from "../api/client";
import Header from "../components/Header";
import Nav from "../components/Nav";
import StatusBanner from "../components/StatusBanner";
import { useDriverGrades } from "../hooks/useDriverGrades";
import type { LayoutContext } from "./useLayoutData";

export default function Layout() {
  const {
    status,
    drivers,
    meta,
    season,
    currentRound,
    lastUpdated,
    message,
    refresh,
    refreshing,
    refreshError,
  } = useDriverGrades();

  // Race Summary depends on FastF1's live-timing feed, which blocks requests
  // from Replit's IP ranges — the backend reports whether that's the case so
  // the tab doesn't lead somewhere guaranteed to fail. Defaults to shown so
  // there's no flash on environments where it works (the check resolves
  // near-instantly; it's a plain env var read, not a FastF1 call).
  const [raceSummaryAvailable, setRaceSummaryAvailable] = useState(true);

  useEffect(() => {
    fetchHealth()
      .then((health) => setRaceSummaryAvailable(health.race_summary_available))
      .catch(() => {});
  }, []);

  const location = useLocation();

  const context: LayoutContext | null =
    meta && season != null && currentRound != null
      ? { drivers, meta, season, currentRound }
      : null;

  return (
    <>
      <Header
        season={season}
        currentRound={currentRound}
        lastUpdated={lastUpdated}
        onRefresh={refresh}
        refreshing={refreshing}
        refreshError={refreshError}
      />
      <Nav raceSummaryAvailable={raceSummaryAvailable} />

      {status !== "ok" && <StatusBanner status={status} message={message} onRetry={refresh} />}

      {status === "ok" && context && (
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
          >
            <Outlet context={context} />
          </motion.div>
        </AnimatePresence>
      )}
    </>
  );
}
