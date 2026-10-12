import RefreshButton from "./RefreshButton";

interface Props {
  season: number | null;
  isPastSeason: boolean;
  currentRound: number | null;
  lastUpdated: string | null;
  onRefresh: () => void;
  refreshing: boolean;
  refreshError: string | null;
}

export default function Header({
  season,
  isPastSeason,
  currentRound,
  lastUpdated,
  onRefresh,
  refreshing,
  refreshError,
}: Props) {
  let subtitle: string;
  if (isPastSeason) {
    subtitle = currentRound != null ? `Final standings · ${currentRound} rounds` : "Loading data…";
  } else {
    subtitle =
      (currentRound != null ? `Round ${currentRound} · ` : "") +
      (lastUpdated ? `Updated ${new Date(lastUpdated).toLocaleString()}` : "Loading data…");
  }

  return (
    <div className="header">
      <div className="header-left">
        <div className="header-logo">F1</div>
        <div>
          <h1>Driver Grades {season ?? ""}</h1>
          <div className="subtitle">{subtitle}</div>
        </div>
      </div>
      {/* A finished season's results never change: nothing to refresh. */}
      {!isPastSeason && (
        <RefreshButton onRefresh={onRefresh} refreshing={refreshing} error={refreshError} />
      )}
    </div>
  );
}
