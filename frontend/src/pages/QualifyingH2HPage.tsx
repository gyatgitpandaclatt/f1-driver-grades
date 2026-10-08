import type { DriverGrade, QualH2HPair } from "../api/types";
import H2HBar from "../components/H2HBar";
import { useLayoutData } from "../layout/useLayoutData";

// Pairings in the order of the grades table, by the better-ranked driver of
// each pair; the longer pairing first when they share that driver.
function orderPairs(pairs: QualH2HPair[], drivers: DriverGrade[]): QualH2HPair[] {
  const rank = new Map(drivers.map((d, i) => [d.driver_code, i]));
  const best = (p: QualH2HPair) =>
    Math.min(rank.get(p.driver_a) ?? Infinity, rank.get(p.driver_b) ?? Infinity);
  return [...pairs].sort((x, y) => best(x) - best(y) || y.races - x.races);
}

export default function QualifyingH2HPage() {
  const { drivers, meta } = useLayoutData();
  const byCode = new Map(drivers.map((d) => [d.driver_code, d]));
  const pairs = orderPairs(meta.qual_h2h_pairs, drivers);

  return (
    <div className="panel">
      <h2>Qualifying Head-to-Head (Teammates)</h2>
      <p className="model-note">
        How often each driver out-qualified their teammate this season, counted over the
        races the two shared a car.
      </p>
      {pairs.length === 0 && <p className="model-note">Not enough teammate data yet.</p>}
      {pairs.map((p) => (
        <div key={`${p.constructor}-${p.driver_a}-${p.driver_b}`} className="h2h-pair">
          <div className="h2h-constructor">
            {p.constructor} · {p.races} {p.races === 1 ? "race" : "races"}
          </div>
          <H2HBar
            leftName={byCode.get(p.driver_a)?.driver_name ?? p.driver_a}
            leftCode={p.driver_a}
            leftWins={p.a_wins}
            rightName={byCode.get(p.driver_b)?.driver_name ?? p.driver_b}
            rightCode={p.driver_b}
            rightWins={p.b_wins}
          />
        </div>
      ))}
    </div>
  );
}
