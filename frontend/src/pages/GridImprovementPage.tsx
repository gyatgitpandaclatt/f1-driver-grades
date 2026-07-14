import DriverBarChart from "../components/DriverBarChart";
import { useLayoutData } from "../layout/useLayoutData";

export default function GridImprovementPage() {
  const { drivers } = useLayoutData();

  const data = drivers.map((d) => ({
    code: d.driver_code,
    name: d.driver_name,
    value: d.grid_score,
  }));

  return (
    <div className="panel">
      <h2>Grid Improvement Score</h2>
      <p className="model-note">
        Based on average finishing position relative to grid position across the season.
        Above the line (50) means gaining places on race day more often than losing them.
      </p>
      <DriverBarChart data={data} neutral={50} />
    </div>
  );
}
