import { motion } from "framer-motion";
import { type CSSProperties, type ReactNode, useMemo, useState } from "react";
import type { DriverGrade } from "../api/types";
import { teamColor } from "../theme/teams";
import { GRADE_ORDER } from "../theme/theme";
import GradeBadge from "./GradeBadge";
import Trophy from "./Trophy";

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

// "Andrea Kimi Antonelli" -> ["Andrea Kimi", "Antonelli"], the way the TV
// graphics set a name; a "Jr." stays with the surname.
export function splitName(name: string): [string, string] {
  const parts = name.split(" ");
  const take = parts.length > 2 && /^(Jr\.?|Sr\.?)$/.test(parts[parts.length - 1]) ? 2 : 1;
  return [parts.slice(0, -take).join(" "), parts.slice(-take).join(" ")];
}

function sortValue(driver: DriverGrade, key: SortKey): number | string {
  if (key === "grade") return GRADE_ORDER[driver.grade] ?? 0;
  return driver[key] as number | string;
}

export default function DriverTable({
  drivers,
  season,
  droppedScores = false,
  footer,
}: {
  drivers: DriverGrade[];
  season: number;
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
      <table className="grades-table">
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
          </tr>
        </thead>
        <tbody>
          {sorted.map((d) => {
            const [first, surname] = splitName(d.driver_name);
            const unplaced = UNPLACED[d.position_text];
            return (
            <motion.tr
              key={d.driver_code}
              layout
              transition={{ type: "spring", stiffness: 500, damping: 40 }}
              className={d.grade === "S" ? "row-s" : undefined}
              // The team's colour runs down the row's left edge.
              style={{ "--team": teamColor(d.constructor, season) } as CSSProperties}
            >
              <td title={unplaced?.title}>
                {/* Painted like a grid slot; the champion's like a pit board. */}
                <span className={d.position === 1 && !unplaced ? "pos-slot pit-board" : "pos-slot"}>
                  {unplaced?.label ?? d.position}
                </span>
              </td>
              <td>
                <span className="driver-cell">
                  <span className="driver-first">{first}</span>
                  <span className="driver-surname">{surname}</span>
                </span>
              </td>
              <td>
                <span className="team-cell">
                  <i className="team-dot" aria-hidden="true" />
                  {d.constructor}
                </span>
              </td>
              <td>{Number.isInteger(d.points) ? d.points : +d.points.toFixed(2)}</td>
              <td className="composite-cell">{d.composite.toFixed(1)}</td>
              <td>
                <span className="grade-cell">
                  <GradeBadge grade={d.grade} />
                  {d.grade === "S" && <Trophy />}
                </span>
              </td>
              <td>{d.season_label}</td>
            </motion.tr>
            );
          })}
        </tbody>
      </table>
      {footer}
    </div>
  );
}
