import { GRADE_ORDER } from "../theme/theme";
import { useLayoutData } from "../layout/useLayoutData";

const GRADE_LABELS: Record<string, string> = {
  S: "Elite",
  A: "Top tier",
  B: "Competitive",
  C: "Mid-field",
  D: "Struggling",
};

const LABEL_DISPLAY: Record<string, string> = {
  overperformed: "Overperformed",
  underperformed: "Underperformed",
  overperformer: "Overperformer",
  underperformer: "Underperformer",
  expected: "Expected",
  no_qualifying_data: "No qualifying data",
};

function pct(part: number, total: number): string {
  return total > 0 ? `${((part / total) * 100).toFixed(0)}%` : "0%";
}

function pts(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

export default function MethodologyPage() {
  const { drivers, meta, season, currentRound, isCurrentSeason } = useLayoutData();

  const gradeCounts: Record<string, number> = { S: 0, A: 0, B: 0, C: 0, D: 0 };
  const seasonLabelCounts: Record<string, number> = {
    expected: 0,
    overperformer: 0,
    underperformer: 0,
  };
  for (const d of drivers) {
    gradeCounts[d.grade] = (gradeCounts[d.grade] ?? 0) + 1;
    seasonLabelCounts[d.season_label] = (seasonLabelCounts[d.season_label] ?? 0) + 1;
  }

  const {
    performance_label_distribution: raceDist,
    total_race_entries: totalRaces,
    min_races_for_grade: minRaces,
    excluded_drivers: excluded,
    rookie_season_threshold: rookieThreshold,
    constructor_tiers: tiers,
    grid_as_qualifying_rounds: gridRounds,
    constructor_tiers_source: tiersSource,
    makes_with_privateers: privateerMakes,
  } = meta;
  // The 1950s left dozens out (the Indianapolis 500's field alone): name the
  // most-raced, and fold the rest away.
  const excludedText = (d: { driver_name: string; races: number }) =>
    `${d.driver_name} (${d.races} ${d.races === 1 ? "race" : "races"})`;
  const EXCLUDED_SHOWN = 12;
  const rookies = drivers.filter((d) => d.is_rookie);
  const standingsWhen = isCurrentSeason ? "standings so far" : "final standings";
  // From the graded drivers' own counts: totalRaces also holds the entries of
  // drivers below the minimum race count, who are not in `drivers`.
  const avgRacesPerDriver =
    drivers.length > 0
      ? (drivers.reduce((sum, d) => sum + d.races, 0) / drivers.length).toFixed(1)
      : "0";

  return (
    <div className="panel prose">
      <h2>Scoring Methodology</h2>
      <p className="caption">
        {isCurrentSeason
          ? `Live snapshot: ${season} season, through round ${currentRound}`
          : `Final: the complete ${season} season, all ${currentRound} rounds`}
        , {drivers.length} drivers, {totalRaces} total race entries.
      </p>

      <h3>Composite Score Components</h3>
      <p>
        The final grade is derived from a composite score combining normalized factors,
        each scaled 0–100, plus a handful of flat bonuses/penalties:
      </p>
      <ul>
        <li>
          <strong>Championship Points Score (22% weight)</strong> — normalized by the
          maximum points total in the field; rewards consistency and race wins.
        </li>
        <li>
          <strong>Championship Position Score (19% weight)</strong> — championship position
          from P1 (100 pts) down to the last classified position (0 pts); reflects title
          contention.
        </li>
        <li>
          <strong>Performance Consistency Score (17.5% weight)</strong> — overperformance
          share minus underperformance share, scaled and offset; captures race-to-race
          execution vs. expectations.
        </li>
        <li>
          <strong>Grid-to-Finish Improvement Score (17.5% weight)</strong> — average places
          gained from qualifying position to finishing position, scaled around 50; drivers
          who gain positions earn higher scores, and drivers who lose them score below 50.
        </li>
        <li>
          <strong>Teammate Points Ratio Score (15% weight)</strong> —{" "}
          {season >= 2021 ? "points (Grand Prix and sprint)" : "points"} relative to the
          teammate&rsquo;s, counted only over the weekends the two shared a car; isolates driver
          value from car performance.
        </li>
        <li>
          <strong>Qualifying Score (15% weight)</strong> — a composite of three
          sub-components:
          <ul>
            <li>Average qualifying position vs. field (60% sub-weight): best avg = 100, worst avg = 0</li>
            <li>Pole position rate (10% sub-weight): scaled by the field's maximum pole frequency</li>
            <li>Teammate qualifying head-to-head (30% sub-weight): percentage of races out-qualifying teammate</li>
          </ul>
        </li>
        <li>
          <strong>Season Label Bonus</strong> (flat +4 for overperformer, 0 for expected, −4
          for underperformer) — rewards or penalizes the macro-level consistency
          classification.
        </li>
        <li>
          <strong>ML Model Agreement Bonus</strong> (flat +0.5 if the season label matches
          the Random Forest model's predicted label, −0.5 otherwise) — a small confidence
          signal from the trained classifier.
        </li>
        <li>
          <strong>Car Strength Tier Bonus</strong> (flat, 0–6) — rewards drivers in weaker
          cars to offset the advantage of driving a faster car. Each car&rsquo;s tier comes from
          {tiersSource === "results" ? (
            <> its constructor&rsquo;s place by points in the {season} race results (there was
              no constructors&rsquo; championship until 1958)</>
          ) : (
            <> its team&rsquo;s place in the {season} constructors&rsquo; championship ({standingsWhen})</>
          )}
          : P1 earns +0 and P9 or lower +6, as in the table below. A driver who changed teams
          is scored on the car they raced most.
        </li>
        <li>
          <strong>Rookie Bonus</strong> (flat +2) — applied to drivers with fewer than{" "}
          {rookieThreshold} {rookieThreshold === 1 ? "season" : "seasons"} of F1 experience
          before {season}. A season counts if they started at least half its races, so a
          reserve&rsquo;s stand-in outings don&rsquo;t use up their rookie year, but partial
          seasons add up: a full season&rsquo;s worth of starts counts as one.
          {season < 1975 &&
            " Before 1960, any championship start counts as a season, since most careers then ran largely outside the championship."}{" "}
          {season === 1950
            ? "Nobody counts as a rookie in 1950, the first championship season: the data has no earlier careers to tell the pre-war veterans from the newcomers."
            : rookies.length > 0
              ? `${season} rookies: ${rookies.map((d) => d.driver_name).join(", ")}.`
              : `No graded driver counts as a rookie in ${season}.`}
        </li>
      </ul>

      {tiers.length > 0 && (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Pos</th>
                <th>Constructor</th>
                <th>Points</th>
                <th>Tier</th>
                <th>Tier bonus</th>
              </tr>
            </thead>
            <tbody>
              {tiers.map((t) => (
                <tr key={t.constructor}>
                  <td>{t.position}</td>
                  <td>{t.constructor}</td>
                  <td>{pts(t.points)}</td>
                  <td>{t.tier}</td>
                  <td>+{t.tier_bonus}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h3>Grade Boundaries</h3>
      <ul>
        <li><strong>S Grade:</strong> ≥88 points (elite)</li>
        <li><strong>A Grade:</strong> 71–87 points (top tier)</li>
        <li><strong>B Grade:</strong> 55–70 points (competitive)</li>
        <li><strong>C Grade:</strong> 38–54 points (mid-field)</li>
        <li><strong>D Grade:</strong> &lt;38 points (struggling)</li>
      </ul>
      <div className="stat-grid">
        {Object.keys(GRADE_ORDER)
          .sort((a, b) => GRADE_ORDER[b] - GRADE_ORDER[a])
          .map((grade) => (
            <div className="stat-tile" key={grade}>
              <div className="stat-value">{gradeCounts[grade] ?? 0}</div>
              <div className="stat-label">
                {grade} — {GRADE_LABELS[grade]}
              </div>
            </div>
          ))}
      </div>

      <h3>Performance Classification</h3>
      <p>
        In addition to the letter grade, each driver receives a performance label
        (expected, overperformer, or underperformer) based on race-to-race consistency and
        seasonal aggregation.
      </p>

      <p><strong>Per-race classification.</strong> Each race result is classified independently:</p>
      <ul>
        <li><strong>Overperformed:</strong> finished ≥3 grid positions higher than qualifying</li>
        <li><strong>Underperformed:</strong> finished ≥3 grid positions lower than qualifying, or did not finish (DNF)</li>
        <li><strong>Expected:</strong> finished within ±2 positions of grid position</li>
      </ul>

      <p><strong>Seasonal aggregation (30% threshold filter).</strong> The per-driver seasonal label is assigned as follows:</p>
      <ul>
        <li>Overperformance frequency &gt; underperformance frequency <strong>and</strong> overperformance frequency &gt; 30% of entries → <strong>overperformer</strong></li>
        <li>Underperformance frequency &gt; overperformance frequency <strong>and</strong> underperformance frequency &gt; 30% of entries → <strong>underperformer</strong></li>
        <li>Otherwise → <strong>expected</strong></li>
      </ul>
      <p>
        The 30% threshold filters noise and requires a meaningful pattern before applying a
        label, which prevents volatile drivers with only one or two unusual races from being
        mislabeled.
      </p>

      <p className="caption">
        {isCurrentSeason ? "Current distribution" : "Distribution"} across {totalRaces} race entries (avg. {avgRacesPerDriver} races
        per driver):
      </p>
      <div className="stat-grid">
        {Object.entries(raceDist).map(([label, count]) => (
          <div className="stat-tile" key={label}>
            <div className="stat-value">{count}</div>
            <div className="stat-label">
              {LABEL_DISPLAY[label] ?? label} ({pct(count, totalRaces)})
            </div>
          </div>
        ))}
      </div>
      <p className="caption">Season-level labels across {drivers.length} drivers:</p>
      <div className="stat-grid">
        {Object.entries(seasonLabelCounts).map(([label, count]) => (
          <div className="stat-tile" key={label}>
            <div className="stat-value">{count}</div>
            <div className="stat-label">
              {LABEL_DISPLAY[label] ?? label} ({pct(count, drivers.length)})
            </div>
          </div>
        ))}
      </div>

      <h3>Limitations and Caveats</h3>

      {isCurrentSeason ? (
        <p><strong>Temporal scope.</strong> This analysis is a midseason snapshot through round{" "}
          {currentRound} of the {season} season. Rankings and grades may shift substantially in
          the remaining rounds — any driver, particularly those in transitional roles or new to
          the grid, may see grades change significantly as more data accumulates.</p>
      ) : (
        <p><strong>Temporal scope.</strong> This analysis covers the complete {season} season,
          all {currentRound} rounds, so these grades are final. They are graded against the{" "}
          {season} field only: a grade compares a driver with that season&rsquo;s grid, not with
          other seasons.</p>
      )}

      <p><strong>Minimum race count.</strong> Drivers who have started fewer than half of
        the season&rsquo;s races (never fewer than 2
        {season <= 1960 ? ", and not counting the Indianapolis 500, which had its own field" : ""})
        are left out of the grades and the head-to-head page entirely
        {minRaces != null ? (
          <> — through round {currentRound}, that means fewer than {minRaces}.</>
        ) : (
          <>, though through round {currentRound} nobody has enough races for the rule to apply
            yet, so everyone is shown.</>
        )}{" "}
        A stand-in&rsquo;s handful of races is far too little to grade a season on, and a few
        volatile results would distort both the model and the score range everyone else is
        measured against. Their races still count where they are a fact about someone else:
        the per-race label distribution below, and their teammate&rsquo;s points ratio and
        qualifying head-to-head score. The head-to-head page itself compares each pair of teammates only
        over the races they shared a car, and leaves out pairings shorter than that same bar,
        such as a driver&rsquo;s short stint in another team&rsquo;s car.
        {excluded.length > 0 && (
          <> Left out of the {season} grades:{" "}
            {excluded.slice(0, EXCLUDED_SHOWN).map(excludedText).join(", ")}
            {excluded.length > EXCLUDED_SHOWN ? "" : "."}</>
        )}</p>
      {excluded.length > EXCLUDED_SHOWN && (
        <details className="more-list">
          <summary>and {excluded.length - EXCLUDED_SHOWN} more</summary>
          <p>{excluded.slice(EXCLUDED_SHOWN).map(excludedText).join(", ")}.</p>
        </details>
      )}

      <p><strong>Sample size &amp; volatility.</strong> Only {drivers.length} drivers are graded,
        limiting the robustness of per-driver metrics. Drivers with fewer completed races
        (e.g. those who joined mid-season) have inherently noisier performance estimates — an
        average of {avgRacesPerDriver} races per driver provides moderate confidence but is
        insufficient for some low-mileage entrants. Teammate comparison metrics depend on
        valid, balanced teammate pairings; if a teammate departed mid-season or has few races,
        the teammate points ratio and qualifying head-to-head may not be representative.</p>

      <p><strong>Qualifying head-to-head normalization.</strong> Drivers without a valid
        teammate (e.g. minimal teammate races) default to a neutral 50% qualifying ratio. This
        neutral assumption may mask actual qualifying strength or weakness.</p>

      {gridRounds.length > 0 && (
        <p><strong>Qualifying from the grid.</strong>{" "}
          {gridRounds.length === currentRound
            ? `There is no qualifying data for ${season}`
            : `${gridRounds.length} of the ${season} rounds have no qualifying data`}
          {" "}(the data has none before the mid-1990s), so the starting grid stands in for the
          qualifying order: for the qualifying score, the head-to-head, and the grid-to-finish
          measures. Before grid penalties the two were near enough the same, but a grid slot
          left empty or unrecorded counts as no qualifying result.</p>
      )}

      {privateerMakes.length > 0 && (
        <p><strong>Privateers as teammates.</strong> The data records the make of car, not who
          entered it, so drivers of the same make count as teammates in the points ratio and the
          head-to-head, a works car and a private one included. In {season}{" "}
          {privateerMakes.join(", ")} ran five or more cars in a Grand Prix, more than a works
          team entered, so their &ldquo;teammates&rdquo; may include private entries.</p>
      )}

      <p><strong>Grid-to-finish outlier capping.</strong> Average places gained is capped
        at ±8 positions to reduce outlier influence — an exceptional single-race result (e.g.
        gaining 15+ places from a low grid slot) is partially masked in the composite score.</p>

      <p><strong>Constructor strength estimates.</strong> Constructor tiers follow{" "}
        {tiersSource === "results"
          ? "the constructors' points in the Grand Prix results (there was no constructors' championship until 1958)"
          : `the constructors' championship (${standingsWhen})`}, which mixes car pace with driver
        performance and doesn&rsquo;t account for in-season car development. Teams with large
        mid-season upgrades may be over- or under-penalized by a single tier for the season
        {isCurrentSeason ? ", and early in a season the order rests on only a handful of races" : ""}.</p>

      <p><strong>Machine learning generalization.</strong> The Random Forest and Logistic
        Regression models are trained on this season's small driver cohort via
        leave-one-out cross-validation. Their accuracy is specific to this dataset and season,
        and should not be assumed to generalize to other years or series.</p>

      <p><strong>Composite score sensitivity.</strong> The final grade is sensitive to the
        weights assigned to each component. Small changes to these weights could shift drivers
        between grade boundaries; the boundaries themselves are chosen for clarity but are
        somewhat arbitrary.</p>

      <p><strong>Missing context.</strong> This analysis does not account for:</p>
      <ul>
        <li>Driver injuries, illness, or personal circumstances</li>
        <li>Technical failures or car reliability differences</li>
        <li>Regulatory changes mid-season</li>
        <li>Rookie drivers' learning curves</li>
        <li>Driver trades or contract terminations partway through the season</li>
      </ul>
      <p>Such factors may significantly impact performance but are not captured in the quantitative model.</p>
    </div>
  );
}
