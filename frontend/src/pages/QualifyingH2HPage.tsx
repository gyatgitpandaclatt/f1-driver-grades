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
  const { drivers, meta, season, currentRound } = useLayoutData();
  const byCode = new Map(drivers.map((d) => [d.driver_code, d]));
  const pairs = orderPairs(meta.qual_h2h_pairs, drivers);
  // Makes that ran five or more cars in a race had private entries too (the
  // data records the make, not the entrant): their pairings may not be
  // teammates, so they are grouped by make and folded away.
  const shared = new Set(meta.makes_with_privateers);
  const teamPairs = pairs.filter((p) => !shared.has(p.constructor));
  const makePairs = meta.makes_with_privateers
    .map((make) => ({ make, pairs: pairs.filter((p) => p.constructor === make) }))
    .filter((group) => group.pairs.length > 0);

  const pairCard = (p: QualH2HPair, showMake = true) => (
    <div key={`${p.constructor}-${p.driver_a}-${p.driver_b}`} className="h2h-pair">
      <div className="h2h-constructor">
        {showMake ? `${p.constructor} · ` : ""}
        {p.races} {p.races === 1 ? "race" : "races"}
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
  );

  return (
    <div className="panel">
      <h2>Qualifying Head-to-Head (Teammates)</h2>
      <p className="model-note">
        How often each driver out-qualified their teammate this season, counted over the
        races the two shared a car.
      </p>
      {meta.grid_as_qualifying_rounds.length > 0 && (
        <p className="model-note">
          {meta.grid_as_qualifying_rounds.length === currentRound
            ? `There is no qualifying data for ${season}`
            : `There is no qualifying data for ${meta.grid_as_qualifying_rounds.length} of the ${season} rounds`}
          , so the starting grid stands in for the qualifying order.
        </p>
      )}
      {pairs.length === 0 && <p className="model-note">Not enough teammate data yet.</p>}
      {teamPairs.map((p) => pairCard(p))}
      {makePairs.length > 0 && (
        <>
          <h3>Makes with private entries</h3>
          <p className="model-note">
            {makePairs.map((g) => g.make).join(", ")} ran five or more cars in a Grand Prix in{" "}
            {season}, more than a works team entered. The data records the make of car, not who
            entered it, so these pairings may include private entries alongside the works team.
          </p>
          {makePairs.map((group) => (
            <details key={group.make} className="more-list">
              <summary>
                {group.make} · {group.pairs.length} {group.pairs.length === 1 ? "pairing" : "pairings"}
              </summary>
              {group.pairs.map((p) => pairCard(p, false))}
            </details>
          ))}
        </>
      )}
    </div>
  );
}
