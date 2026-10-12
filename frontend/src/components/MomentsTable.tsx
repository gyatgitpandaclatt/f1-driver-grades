import type { Moment } from "../api/types";

const KIND_LABELS: Record<string, string> = {
  title_decided: "Title decided",
  lead_change: "Lead change",
  points_swing: "Points swing",
  contender_duel: "Close finish",
  first_win: "First win",
  win_outside_top: "Win",
  first_podium: "First podium",
  rookie_first_points: "Rookie",
  crucial_points: "Crucial points",
};

export default function MomentsTable({ moments }: { moments: Moment[] }) {
  if (moments.length === 0) return null;
  return (
    <table className="moments-table">
      <thead>
        <tr>
          <th>Round</th>
          <th>Race</th>
          <th>Moment</th>
        </tr>
      </thead>
      <tbody>
        {moments.map((m) => (
          <tr key={`${m.round}-${m.headline}`}>
            <td>{m.round}</td>
            <td>{m.race_name}</td>
            <td className="wrap">
              <span className="moment-tags">
                {m.kinds.map((kind) => (
                  <span key={kind} className={`moment-tag ${kind}`}>
                    {KIND_LABELS[kind] ?? kind}
                  </span>
                ))}
              </span>
              {m.headline}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
