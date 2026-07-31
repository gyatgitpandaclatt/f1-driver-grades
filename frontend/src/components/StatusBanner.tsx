import type { UIStatus } from "../hooks/useDriverGrades";

interface Props {
  status: UIStatus;
  message: string | null;
  onRetry: () => void;
  loadingMessage?: string;
}

export default function StatusBanner({ status, message, onRetry, loadingMessage }: Props) {
  if (status === "loading") {
    return <div className="status-banner">{loadingMessage ?? "Loading driver grades…"}</div>;
  }

  if (status === "no_data") {
    return (
      <div className="status-banner">
        {message ?? "No completed races found for this season yet."}
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="status-banner error">
        <div>{message ?? "Something went wrong."}</div>
        <button onClick={onRetry}>Retry</button>
      </div>
    );
  }

  return null;
}
