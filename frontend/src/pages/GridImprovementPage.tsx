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
        Based on average places gained from the starting grid slot (after penalties; a pit-lane
        start counts as the back of the field) to the finish, over the races run to the end.
        Places are counted among the cars that ran to the end, so a retirement ahead isn&rsquo;t
        a place gained.
        Above the line (50) means gaining places on race day on average; below it, losing them.
      </p>
      <DriverBarChart data={data} neutral={50} />
    </div>
  );
}
