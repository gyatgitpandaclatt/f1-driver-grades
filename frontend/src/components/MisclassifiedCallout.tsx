import type { MisclassifiedEntry } from "../api/types";

export default function MisclassifiedCallout({
  entries,
  names = {},
}: {
  entries: MisclassifiedEntry[];
  // Code -> name: before the 2000s the codes are made up, so name the driver.
  names?: Record<string, string>;
}) {
  return (
    <div className="panel">
      <h2>Misclassified Drivers</h2>
      {entries.length === 0 ? (
        <p className="model-note">All predictions matched actual labels this update.</p>
      ) : (
        <ul className="misclassified-list">
          {entries.map((e) => (
            <li key={e.driver_code}>
              <strong>{names[e.driver_code] ?? e.driver_code}</strong>
              {names[e.driver_code] ? ` (${e.driver_code})` : ""} — actual: {e.actual_label}, predicted:{" "}
              {e.predicted_label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
