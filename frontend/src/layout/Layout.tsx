import { Outlet } from "react-router-dom";
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

      {status === "ok" && context && <Outlet context={context} />}
    </>
  );
}
