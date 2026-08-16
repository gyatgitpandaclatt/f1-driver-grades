import NarrativeSection from "../components/NarrativeSection";
import PositionChangesChart from "../components/PositionChangesChart";
import RefreshButton from "../components/RefreshButton";
import StatusBanner from "../components/StatusBanner";
import { useRaceSummary } from "../hooks/useRaceSummary";

export default function RaceSummaryPage() {
  const {
    status,
    season,
    round,
    raceName,
    lastUpdated,
    sections,
    context,
    charts,
    message,
    refresh,
    refreshing,
    refreshError,
  } = useRaceSummary();

  if (status !== "ok" || !sections || !context || !charts) {
    return (
      <div className="panel">
        <h2>Race Summary</h2>
        <StatusBanner
          status={status}
          message={message}
          onRetry={refresh}
          loadingMessage="Loading race summary… this can take a moment while Claude writes the narrative."
        />
      </div>
    );
  }

  const podium = context.final_classification.slice(0, 3).map((entry) => entry.driver_code);
  const pitStops = [...context.pit_stops].sort((a, b) => a.lap_number - b.lap_number);

  return (
    <div className="panel prose">
      <h2>{raceName} — Race Summary</h2>
      <p className="caption">
        {season} · Round {round}
        {lastUpdated ? ` · Updated ${new Date(lastUpdated).toLocaleString()}` : ""}
      </p>
      <RefreshButton onRefresh={refresh} refreshing={refreshing} error={refreshError} />

      <h3>Race Summary</h3>
      <NarrativeSection text={sections.summary} />

      <h3>Lap-by-Lap Highlights</h3>
      <PositionChangesChart data={charts.position_series} highlightDrivers={podium} />
      <NarrativeSection text={sections.lap_highlights} />

      <h3>Pit Stop Analysis</h3>
      <NarrativeSection text={sections.pit_analysis} />
      {pitStops.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Driver</th>
              <th>Lap</th>
              <th>Stop #</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            {pitStops.map((stop, i) => (
              <tr key={i}>
                <td>{stop.driver}</td>
                <td>{stop.lap_number}</td>
                <td>{stop.stop_number}</td>
                <td>{stop.duration_seconds != null ? `${stop.duration_seconds.toFixed(1)}s` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3>Overtakes &amp; Battles</h3>
      <NarrativeSection text={sections.overtakes_battles} />
      {context.overtakes.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Lap</th>
              <th>Overtake</th>
            </tr>
          </thead>
          <tbody>
            {context.overtakes.map((o, i) => (
              <tr key={i}>
                <td>{o.lap}</td>
                <td>
                  {o.overtaking_driver} ahead of {o.overtaken_driver}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3>Driver of the Day</h3>
      <NarrativeSection text={sections.driver_of_the_day} />
    </div>
  );
}
