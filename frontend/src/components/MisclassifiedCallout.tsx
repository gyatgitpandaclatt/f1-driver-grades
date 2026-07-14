import type { MisclassifiedEntry } from "../api/types";

export default function MisclassifiedCallout({ entries }: { entries: MisclassifiedEntry[] }) {
  return (
    <div className="panel">
      <h2>Misclassified Drivers</h2>
      {entries.length === 0 ? (
        <p className="model-note">All predictions matched actual labels this update.</p>
      ) : (
        <ul className="misclassified-list">
          {entries.map((e) => (
            <li key={e.driver_code}>
              <strong>{e.driver_code}</strong> — actual: {e.actual_label}, predicted: {e.predicted_label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
