import DriverTable from "../components/DriverTable";
import FeatureImportanceChart from "../components/FeatureImportanceChart";
import PredictedVsActualChart from "../components/PredictedVsActualChart";
import MisclassifiedCallout from "../components/MisclassifiedCallout";
import { useLayoutData } from "../layout/useLayoutData";

export default function DriverGradesPage() {
  const { drivers, meta } = useLayoutData();

  return (
    <>
      <DriverTable drivers={drivers} />
      {meta.model_note && <p className="model-note">{meta.model_note}</p>}
      <div className="charts-row">
        <FeatureImportanceChart data={meta.feature_importances} note={meta.model_note} />
        <PredictedVsActualChart data={meta.predicted_vs_actual} />
      </div>
      <MisclassifiedCallout entries={meta.misclassified} />
    </>
  );
}
