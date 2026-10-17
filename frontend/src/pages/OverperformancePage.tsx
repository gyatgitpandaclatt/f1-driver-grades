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
        Based on the share of races each driver finished well ahead of their starting grid
        slot (after penalties; a pit-lane start counts as the back of the field) vs. well behind
        it, out in a crash, or disqualified. Other retirements (on the first lap, mechanical, or
        with no cause recorded) are left out. Above the line (50) means overperforming more
        often than underperforming.
      </p>
      <DriverBarChart data={data} neutral={50} />
    </div>
  );
}
