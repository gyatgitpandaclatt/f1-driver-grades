import { Navigate, useLocation } from "react-router";
import MomentsTable from "../components/MomentsTable";
import NarrativeSection from "../components/NarrativeSection";
import PositionChangesChart from "../components/PositionChangesChart";
import RefreshButton from "../components/RefreshButton";
import StatusBanner from "../components/StatusBanner";
import { useSeasonSummary } from "../hooks/useSeasonSummary";
import { useLayoutData } from "../layout/useLayoutData";

function pts(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function SeasonSummary({ season }: { season: number }) {
  const {
    status,
    rounds,
    champion,
    sections,
    context,
    charts,
    snapshot,
    message,
    refresh,
    refreshing,
    refreshError,
  } = useSeasonSummary(season);

  if (status !== "ok" || !sections || !context || !charts || !champion) {
    return (
      <div className="panel">
        <h2>{season} Season Summary</h2>
        <StatusBanner
          status={status}
          message={message}
          onRetry={refresh}
          loadingMessage="Loading season summary… the first visit to a season can take a minute while its results are gathered and Gemini writes the review."
        />
      </div>
    );
  }

  const raceNames = new Map(charts.rounds.map((r) => [r.round, r.race_name]));
  const decided = context.title_decided;

  return (
    <div className="panel prose">
      <h2>{season} — Season Summary</h2>
      <p className="caption">
        Champion: {champion.driver_name} ({champion.constructor}), {pts(champion.points)} pts ·{" "}
        {rounds} rounds · Title decided at round {decided.round} ({decided.race_name})
        {decided.rounds_left > 0
          ? `, with ${decided.rounds_left} ${decided.rounds_left === 1 ? "round" : "rounds"} to go`
          : ", the final round"}
      </p>
      {/* A saved snapshot is fixed: rewriting it is the snapshot script's job. */}
      {!snapshot && (
        <RefreshButton onRefresh={refresh} refreshing={refreshing} error={refreshError} />
      )}

      <h3>Season Summary</h3>
      <NarrativeSection text={sections.summary} />

      <h3>Championship Battle</h3>
      <PositionChangesChart
        data={charts.standings_series}
        highlightDrivers={charts.highlight_drivers}
        xKey="round"
        xLabel="Round"
        yLabel="Championship position"
        describeX={(round) => `Round ${round} · ${raceNames.get(round) ?? ""}`}
      />
      <NarrativeSection text={sections.championship_progression} />

      <h3>Quarterly Analysis</h3>
      <NarrativeSection text={sections.quarterly_analysis} />
      <table>
        <thead>
          <tr>
            <th>Quarter</th>
            <th>Rounds</th>
            <th>Leader after</th>
            <th>Most points</th>
            <th>Winners</th>
          </tr>
        </thead>
        <tbody>
          {context.quarters.map((q) => (
            <tr key={q.label}>
              <td>{q.label}</td>
              <td>
                {q.first_round}–{q.last_round}
              </td>
              <td>
                {q.leader}
                {q.margin != null ? ` (+${pts(q.margin)} on ${q.runner_up})` : ""}
              </td>
              <td>{q.top_scorers.map((d) => `${d.driver_code} ${pts(d.points)}`).join(", ")}</td>
              <td>{q.winners.map((w) => `${w.driver_code} ×${w.wins}`).join(", ") || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Crucial Moments — The Championship</h3>
      <NarrativeSection text={sections.championship_moments} />
      <MomentsTable moments={context.championship_moments} />

      <h3>Crucial Moments — Beyond the Title Fight</h3>
      <NarrativeSection text={sections.other_moments} />
      <MomentsTable moments={context.other_moments} />
      {context.part_time_drivers.length > 0 && (
        <div className="footnotes">
          <h4>Footnotes: part-time drivers</h4>
          <p className="caption">
            Drivers who started fewer than half of the season&rsquo;s races. They are left out of
            the grades and the title story, and listed here instead.
          </p>
          <ol>
            {context.part_time_drivers.map((d) => (
              <li key={d.driver_code}>{d.summary}</li>
            ))}
          </ol>
        </div>
      )}

      <h3>Driver of the Season</h3>
      <NarrativeSection text={sections.driver_of_the_season} />
    </div>
  );
}

// Finished seasons only: the current season keeps the race summary.
export default function SeasonSummaryPage() {
  const { season, isCurrentSeason } = useLayoutData();
  const { search } = useLocation();
  if (isCurrentSeason) {
    return <Navigate to={{ pathname: "/race-summary", search }} replace />;
  }
  return <SeasonSummary season={season} />;
}
