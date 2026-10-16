import { motion } from "framer-motion";
import { type ReactNode, useMemo, useState } from "react";
import type { DriverGrade } from "../api/types";
import { GRADE_ORDER } from "../theme/theme";
import GradeBadge from "./GradeBadge";

type SortKey = "position" | "driver_name" | "constructor" | "points" | "composite" | "grade" | "season_label";

interface Column {
  key: SortKey;
  label: string;
}

const COLUMNS: Column[] = [
  { key: "position", label: "Pos" },
  { key: "driver_name", label: "Driver" },
  { key: "constructor", label: "Constructor" },
  { key: "points", label: "Points" },
  { key: "composite", label: "Composite" },
  { key: "grade", label: "Grade" },
  { key: "season_label", label: "Season Label" },
];

// Drivers the championship didn't place share the position after the last
// classified one; show why instead of a number none of them held.
const UNPLACED: Record<string, { label: string; title: string }> = {
  "-": { label: "NC", title: "Not classified in the championship" },
  D: { label: "DSQ", title: "Disqualified from the championship" },
  E: { label: "EX", title: "Excluded from the championship" },
};

function sortValue(driver: DriverGrade, key: SortKey): number | string {
  if (key === "grade") return GRADE_ORDER[driver.grade] ?? 0;
  return driver[key] as number | string;
}

export default function DriverTable({
  drivers,
  droppedScores = false,
  footer,
}: {
  drivers: DriverGrade[];
  droppedScores?: boolean;
  footer?: ReactNode;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("composite");
  const [ascending, setAscending] = useState(false);

  const sorted = useMemo(() => {
    const copy = [...drivers];
    copy.sort((a, b) => {
      const av = sortValue(a, sortKey);
      const bv = sortValue(b, sortKey);
      const cmp = typeof av === "string" ? av.localeCompare(bv as string) : av - (bv as number);
      return ascending ? cmp : -cmp;
    });
    return copy;
  }, [drivers, sortKey, ascending]);

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setAscending((a) => !a);
    } else {
      setSortKey(key);
      setAscending(false);
    }
  };

  return (
    <div className="panel">
      <h2>Driver Grades</h2>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  title={
                    col.key === "points" && droppedScores
                      ? "Championship points: only each driver's best results counted this season"
                      : undefined
                  }
                >
                  {col.key === "points" && droppedScores ? "Points (counted)" : col.label}
                  {sortKey === col.key ? (ascending ? " ▲" : " ▼") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((d) => (
              <motion.tr
                key={d.driver_code}
                layout
                transition={{ type: "spring", stiffness: 500, damping: 40 }}
              >
                <td title={UNPLACED[d.position_text]?.title}>
                  {UNPLACED[d.position_text]?.label ?? d.position}
                </td>
                <td>{d.driver_name}</td>
                <td>{d.constructor}</td>
                <td>{Number.isInteger(d.points) ? d.points : +d.points.toFixed(2)}</td>
                <td>{d.composite.toFixed(1)}</td>
                <td>
                  <GradeBadge grade={d.grade} />
                </td>
                <td>{d.season_label}</td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
      {footer}
    </div>
  );
}
