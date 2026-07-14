interface Props {
  onRefresh: () => void;
  refreshing: boolean;
  error: string | null;
}

export default function RefreshButton({ onRefresh, refreshing, error }: Props) {
  return (
    <div>
      <button className="refresh-button" onClick={onRefresh} disabled={refreshing}>
        {refreshing ? "Refreshing…" : "Refresh"}
      </button>
      {error && <div className="refresh-error">{error}</div>}
    </div>
  );
}
