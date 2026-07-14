import DriverBarChart from "../components/DriverBarChart";
import { useLayoutData } from "../layout/useLayoutData";

export default function OverperformancePage() {
  const { drivers } = useLayoutData();

  const data = drivers.map((d) => ({
    code: d.driver_code,
    name: d.driver_name,
    value: d.perf_score,
  }));

  return (
    <div className="panel">
      <h2>Overperformance Score</h2>
      <p className="model-note">
        Based on the share of races each driver finished well ahead of their qualifying
        position vs. well behind it. Above the line (50) means overperforming more often
        than underperforming.
      </p>
      <DriverBarChart data={data} neutral={50} />
    </div>
  );
}
