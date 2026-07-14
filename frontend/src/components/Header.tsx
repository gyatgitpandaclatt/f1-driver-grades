import RefreshButton from "./RefreshButton";

interface Props {
  season: number | null;
  currentRound: number | null;
  lastUpdated: string | null;
  onRefresh: () => void;
  refreshing: boolean;
  refreshError: string | null;
}

export default function Header({
  season,
  currentRound,
  lastUpdated,
  onRefresh,
  refreshing,
  refreshError,
}: Props) {
  return (
    <div className="header">
      <div className="header-left">
        <div className="header-logo">F1</div>
        <div>
          <h1>Driver Grades {season ?? ""}</h1>
          <div className="subtitle">
            {currentRound != null && <>Round {currentRound} · </>}
            {lastUpdated
              ? `Updated ${new Date(lastUpdated).toLocaleString()}`
              : "Loading data…"}
          </div>
        </div>
      </div>
      <RefreshButton onRefresh={onRefresh} refreshing={refreshing} error={refreshError} />
    </div>
  );
}
