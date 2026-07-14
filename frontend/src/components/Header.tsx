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
      <div>
        <h1>F1 {season ?? ""} Driver Grades</h1>
        <div className="subtitle">
          {currentRound != null && <>Through round {currentRound} · </>}
          {lastUpdated
            ? `Last updated ${new Date(lastUpdated).toLocaleString()}`
            : "Loading…"}
        </div>
      </div>
      <RefreshButton onRefresh={onRefresh} refreshing={refreshing} error={refreshError} />
    </div>
  );
}
