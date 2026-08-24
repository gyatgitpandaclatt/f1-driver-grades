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

  if (status === "busy") {
    // Upstream rate limit: the hook is already counting down to a reload, so
    // this is a wait, not a failure. Retry stays available for the impatient.
    return (
      <div className="status-banner">
        <div>{message ?? "The F1 data provider is busy. Retrying shortly…"}</div>
        <button onClick={onRetry}>Retry now</button>
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
