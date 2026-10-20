import { AnimatePresence, MotionConfig, motion } from "framer-motion";
import { useEffect } from "react";
import { useLocation, useOutlet, useSearchParams } from "react-router";
import EraHero from "../components/EraHero";
import Header from "../components/Header";
import Nav from "../components/Nav";
import RaceBackdrop from "../components/RaceBackdrop";
import StatusBanner from "../components/StatusBanner";
import { useDriverGrades } from "../hooks/useDriverGrades";
import { useSeasons } from "../hooks/useSeasons";
import { eraFor } from "../theme/eras";
import type { LayoutContext } from "./useLayoutData";

// "?season=2024" -> 2024. Absent or malformed means the current season.
function parseSeason(raw: string | null): number | null {
  return raw && /^\d{4}$/.test(raw) ? Number(raw) : null;
}

export default function Layout() {
  const [searchParams] = useSearchParams();
  const seasonParam = parseSeason(searchParams.get("season"));
  const { current, seasons } = useSeasons();
  const {
    status,
    drivers,
    meta,
    season,
    isCurrentSeason,
    currentRound,
    lastUpdated,
    message,
    refresh,
    refreshing,
    refreshError,
  } = useDriverGrades(seasonParam);

  const location = useLocation();

  // The season being asked for. Grades still on screen from the previous
  // pick are not shown under it: right after a switch, before the new load
  // has even started, `status` is still "ok" for the old season.
  const selectedSeason = seasonParam ?? current ?? season;
  const loaded = status === "ok" && season != null && season === selectedSeason;
  const shownStatus = status === "ok" && !loaded ? "loading" : status;
  const isPastSeason = loaded
    ? isCurrentSeason === false
    : seasonParam != null && seasonParam !== current;

  const context: LayoutContext | null =
    loaded && meta && season != null && currentRound != null
      ? { drivers, meta, season, isCurrentSeason: isCurrentSeason !== false, currentRound }
      : null;
  // The page element, captured per render. An exiting page keeps the element
  // it was rendered with while it animates out; an <Outlet/> inside it would
  // read the router live and re-render the new page in the exiting tree,
  // which left the content stuck invisible after a tab change.
  const outlet = useOutlet(context ?? undefined);

  // The era's colours and fonts are keyed off <html data-era> in index.css.
  const era = eraFor(selectedSeason);
  useEffect(() => {
    document.documentElement.dataset.era = era.id;
  }, [era.id]);

  return (
    // "user": movement is skipped for visitors who ask for reduced motion.
    <MotionConfig reducedMotion="user">
      <RaceBackdrop era={era.id} />
      <Header
        season={selectedSeason}
        isPastSeason={isPastSeason}
        currentRound={loaded ? currentRound : null}
        lastUpdated={loaded ? lastUpdated : null}
        onRefresh={refresh}
        refreshing={refreshing}
        refreshError={refreshError}
      />
      {/* Keyed on the URL's pick, which is known at once: selectedSeason goes
          from null to the current year when the list loads, which would
          restart the lights mid-sequence. */}
      <EraHero key={seasonParam ?? "current"} era={era} season={selectedSeason} />
      <Nav
        isPastSeason={isPastSeason}
        seasons={seasons}
        currentSeason={current}
        selectedSeason={selectedSeason}
      />

      {shownStatus !== "ok" && (
        <StatusBanner
          status={shownStatus}
          message={message}
          onRetry={refresh}
          loadingMessage={
            isPastSeason && selectedSeason != null
              ? `Loading the ${selectedSeason} season… the first visit to a past season can take a moment.`
              : undefined
          }
        />
      )}

      {context && (
        <AnimatePresence mode="wait">
          <motion.div
            key={`${location.pathname}-${context.season}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
          >
            {outlet}
          </motion.div>
        </AnimatePresence>
      )}
    </MotionConfig>
  );
}
