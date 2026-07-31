import NarrativeSection from "../components/NarrativeSection";
import PositionChangesChart from "../components/PositionChangesChart";
import RefreshButton from "../components/RefreshButton";
import SpeedTraceChart from "../components/SpeedTraceChart";
import StatusBanner from "../components/StatusBanner";
import TireStrategyChart from "../components/TireStrategyChart";
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
          loadingMessage="Loading race summary… this can take a couple of minutes the first time a race's telemetry loads."
        />
      </div>
    );
  }

  const driverOrder = context.final_classification.map((entry) => entry.driver_code);
  const podium = driverOrder.slice(0, 3);

  return (
    <div className="panel prose">
      <h2>{raceName} — Race Summary</h2>
      <p className="caption">
        {season} · Round {round}
        {lastUpdated ? ` · Updated ${new Date(lastUpdated).toLocaleString()}` : ""}
      </p>
      <RefreshButton onRefresh={refresh} refreshing={refreshing} error={refreshError} />

      <h3>Race Summary</h3>
      <p className="caption">{context.weather_summary}</p>
      <NarrativeSection text={sections.summary} />

      <h3>Lap-by-Lap Highlights</h3>
      <PositionChangesChart data={charts.position_series} highlightDrivers={podium} />
      <NarrativeSection text={sections.lap_highlights} />

      <h3>Pit Stop Analysis</h3>
      <TireStrategyChart stints={context.strategies} driverOrder={driverOrder} totalLaps={context.total_laps} />
      <NarrativeSection text={sections.pit_analysis} />

      <h3>Overtakes &amp; Battles</h3>
      <NarrativeSection text={sections.overtakes_battles} />
      {context.overtakes.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Lap</th>
              <th>Overtake</th>
              <th>Track Status</th>
            </tr>
          </thead>
          <tbody>
            {context.overtakes.map((o, i) => (
              <tr key={i}>
                <td>{o.lap}</td>
                <td>
                  {o.overtaking_driver} ahead of {o.overtaken_driver}
                </td>
                <td>{o.track_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3>Telemetry Spotlight</h3>
      <SpeedTraceChart data={charts.speed_traces} />
      <NarrativeSection text={sections.telemetry_spotlight} />

      <h3>Driver of the Day</h3>
      <NarrativeSection text={sections.driver_of_the_day} />
    </div>
  );
}
