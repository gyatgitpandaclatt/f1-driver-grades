import type { DriverGrade } from "../api/types";
import H2HBar from "../components/H2HBar";
import { useLayoutData } from "../layout/useLayoutData";

interface Pair {
  constructor: string;
  a: DriverGrade;
  b: DriverGrade;
}

function buildPairs(drivers: DriverGrade[]): Pair[] {
  const byConstructor = new Map<string, DriverGrade[]>();
  for (const d of drivers) {
    const list = byConstructor.get(d.constructor) ?? [];
    list.push(d);
    byConstructor.set(d.constructor, list);
  }

  const pairs: Pair[] = [];
  for (const [constructor, teamDrivers] of byConstructor) {
    for (let i = 0; i < teamDrivers.length; i++) {
      for (let j = i + 1; j < teamDrivers.length; j++) {
        pairs.push({ constructor, a: teamDrivers[i], b: teamDrivers[j] });
      }
    }
  }
  return pairs;
}

export default function QualifyingH2HPage() {
  const { drivers } = useLayoutData();
  const pairs = buildPairs(drivers);

  return (
    <div className="panel">
      <h2>Qualifying Head-to-Head (Teammates)</h2>
      <p className="model-note">
        How often each driver out-qualified their teammate this season.
      </p>
      {pairs.length === 0 && <p className="model-note">Not enough teammate data yet.</p>}
      {pairs.map(({ constructor, a, b }) => (
        <div key={`${a.driver_code}-${b.driver_code}`} className="h2h-pair">
          <div className="h2h-constructor">{constructor}</div>
          <H2HBar
            leftName={a.driver_name}
            leftCode={a.driver_code}
            leftWins={a.qual_h2h_wins}
            rightName={b.driver_name}
            rightCode={b.driver_code}
            rightWins={b.qual_h2h_wins}
          />
        </div>
      ))}
    </div>
  );
}
