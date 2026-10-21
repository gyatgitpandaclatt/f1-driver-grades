import type { UIStatus } from "../hooks/useDriverGrades";

// A car under its cover in the garage, the way teams hide one overnight:
// shown while the season's grades are being worked out.
function CoveredCar() {
  return (
    <svg className="covered-car" viewBox="0 0 200 60" aria-hidden="true">
      <path
        className="cover"
        d="M8 46 Q10 30 30 28 L52 26 Q70 12 92 12 Q106 12 112 20 L150 24 Q180 26 192 40 L194 48 Z"
      />
      <path className="cover-fold" d="M60 26 Q66 40 62 48 M100 14 Q104 32 98 48 M146 26 Q150 38 146 48" />
      <circle className="cover-tyre" cx={40} cy={50} r={9} />
      <circle className="cover-tyre" cx={164} cy={50} r={9} />
    </svg>
  );
}

interface Props {
  status: UIStatus;
  message: string | null;
  onRetry: () => void;
  loadingMessage?: string;
}

export default function StatusBanner({ status, message, onRetry, loadingMessage }: Props) {
  if (status === "loading") {
    return (
      <div className="status-banner">
        <CoveredCar />
        {loadingMessage ?? "Loading driver grades…"}
      </div>
    );
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

  if (status === "unavailable") {
    // No retry control: the backend has told us this will not come back on
    // its own, and a button that cannot work is worse than no button.
    return (
      <div className="status-banner error">
        {message ?? "This section is unavailable right now."}
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
