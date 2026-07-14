import { AnimatePresence, motion } from "framer-motion";
import { Outlet, useLocation } from "react-router-dom";
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
      <Nav />

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
