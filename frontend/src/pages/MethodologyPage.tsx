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

export default function MethodologyPage() {
  const { drivers, meta, season, currentRound } = useLayoutData();

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

  const { performance_label_distribution: raceDist, total_race_entries: totalRaces } = meta;
  const avgRacesPerDriver = drivers.length > 0 ? (totalRaces / drivers.length).toFixed(1) : "0";

  return (
    <div className="panel prose">
      <h2>Scoring Methodology</h2>
      <p className="caption">
        Live snapshot: {season} season, through round {currentRound}, {drivers.length} drivers,{" "}
        {totalRaces} total race entries.
      </p>

      <h3>Composite Score Components</h3>
      <p>
        The final grade is derived from a composite score combining normalized factors,
        each scaled 0–100, plus a handful of flat bonuses/penalties:
      </p>
      <ul>
        <li>
          <strong>Championship Points Score (25% weight)</strong> — normalized by the
          maximum points total in the field; rewards consistency and race wins.
        </li>
        <li>
          <strong>Championship Position Score (20% weight)</strong> — championship position
          from P1 (100 pts) down to the last classified position (0 pts); reflects title
          contention.
        </li>
        <li>
          <strong>Performance Consistency Score (13% weight)</strong> — overperformance
          share minus underperformance share, scaled and offset; captures race-to-race
          execution vs. expectations.
        </li>
        <li>
          <strong>Grid-to-Finish Improvement Score (12% weight)</strong> — negative average
          finish-minus-grid (better finishes than grid) scaled; drivers who gain positions
          earn higher scores.
        </li>
        <li>
          <strong>Teammate Points Ratio Score (8% weight)</strong> — points relative to the
          highest-scoring teammate on the same constructor; isolates driver value from car
          performance.
        </li>
        <li>
          <strong>Qualifying Score (8% weight)</strong> — a composite of three
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
          cars (Mercedes = 0, Cadillac/Aston Martin = +6) to offset the advantage of
          driving a faster car.
        </li>
        <li>
          <strong>Rookie Bonus</strong> (flat +2) — applied only to drivers in their first
          full F1 season.
        </li>
      </ul>

      <h3>Grade Boundaries</h3>
      <ul>
        <li><strong>S Grade:</strong> ≥80 points (elite)</li>
        <li><strong>A Grade:</strong> 65–79 points (top tier)</li>
        <li><strong>B Grade:</strong> 50–64 points (competitive)</li>
        <li><strong>C Grade:</strong> 35–49 points (mid-field)</li>
        <li><strong>D Grade:</strong> &lt;35 points (struggling)</li>
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
        Current distribution across {totalRaces} race entries (avg. {avgRacesPerDriver} races
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

      <p><strong>Temporal scope.</strong> This analysis is a midseason snapshot through round{" "}
        {currentRound} of the {season} season. Rankings and grades may shift substantially in
        the remaining rounds — any driver, particularly those in transitional roles or new to
        the grid, may see grades change significantly as more data accumulates.</p>

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

      <p><strong>Grid-to-finish outlier capping.</strong> Average finish-minus-grid is capped
        at ±8 positions to reduce outlier influence — an exceptional single-race result (e.g.
        gaining 15+ places from a low grid slot) is partially masked in the composite score.</p>

      <p><strong>Constructor strength estimates.</strong> Constructor tier classifications are
        fixed for the season and don't account for in-season car development. Teams with large
        mid-season upgrades may invalidate the tier assumption, over- or under-penalizing their
        drivers.</p>

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
