import DriverTable from "../components/DriverTable";
import TopDriverCard from "../components/TopDriverCard";
import FeatureImportanceChart from "../components/FeatureImportanceChart";
import PredictedVsActualChart from "../components/PredictedVsActualChart";
import MisclassifiedCallout from "../components/MisclassifiedCallout";
import { useLayoutData } from "../layout/useLayoutData";

export default function DriverGradesPage() {
  const { drivers, meta, season } = useLayoutData();
  const names = Object.fromEntries(drivers.map((d) => [d.driver_code, d.driver_name]));
  const left = meta.excluded_drivers.length;

  return (
    <>
      <TopDriverCard drivers={drivers} season={season} />
      <DriverTable
        drivers={drivers}
        season={season}
        droppedScores={meta.dropped_scores}
        footer={
          left > 0 && meta.min_races_for_grade != null ? (
            <p className="table-note">
              {left} {left === 1 ? "driver" : "drivers"} who started fewer than{" "}
              {meta.min_races_for_grade} races
              {season <= 1960 ? " (not counting the Indianapolis 500)" : ""}{" "}
              {left === 1 ? "isn't" : "aren't"} graded; the Methodology tab lists them.
              {meta.dropped_scores ? " Points are championship points: only each driver's best results counted." : ""}
            </p>
          ) : meta.dropped_scores ? (
            <p className="table-note">Points are championship points: only each driver&rsquo;s best results counted.</p>
          ) : null
        }
      />
      {meta.model_note && <p className="model-note">{meta.model_note}</p>}
      <div className="charts-row">
        <FeatureImportanceChart
          data={meta.feature_importances}
          note={meta.model_note}
          rfMetrics={meta.rf_metrics}
        />
        <PredictedVsActualChart data={meta.predicted_vs_actual} />
      </div>
      <MisclassifiedCallout entries={meta.misclassified} names={names} />
    </>
  );
}
