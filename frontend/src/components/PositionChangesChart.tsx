import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { COLORS } from "../theme/theme";

interface Props {
  data: Record<string, number>[];
  // Driver codes to color + list in the legend (e.g. the podium). Everyone
  // else renders as a muted, unlabeled line — a 20-color legend fights
  // itself, so only the drivers that matter for the story get identity.
  highlightDrivers: string[];
  // The x-axis: laps for a race, rounds for a championship.
  xKey?: string;
  xLabel?: string;
  yLabel?: string;
  // Tooltip heading for an x value; defaults to e.g. "Lap 12".
  describeX?: (x: number) => string;
}

const MUTED_STROKE = COLORS.text;

interface TooltipPayloadEntry {
  dataKey: string;
  value: number;
  color: string;
}

function PositionTooltip({
  active,
  payload,
  label,
  describeX,
}: {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
  label?: number;
  describeX: (x: number) => string;
}) {
  if (!active || !payload?.length) return null;
  const rows = payload
    .filter((p) => typeof p.value === "number")
    .sort((a, b) => a.value - b.value);

  return (
    <div
      style={{
        background: COLORS.surface,
        border: `1px solid ${COLORS.border}`,
        borderRadius: 4,
        padding: 8,
        maxHeight: 280,
        overflowY: "auto",
      }}
    >
      <div style={{ color: COLORS.text, fontWeight: 600, marginBottom: 4 }}>
        {label != null ? describeX(label) : ""}
      </div>
      {rows.map((p) => (
        <div key={p.dataKey} style={{ color: COLORS.textSecondary, fontSize: 12 }}>
          P{p.value} — <span style={{ color: p.color }}>{p.dataKey}</span>
        </div>
      ))}
    </div>
  );
}

export default function PositionChangesChart({
  data,
  highlightDrivers,
  xKey = "lap",
  xLabel = "Lap",
  yLabel = "Position",
  describeX = (x) => `${xLabel} ${x}`,
}: Props) {
  // Every row, not just the first: a driver who joined partway through (a
  // stand-in, in a season chart) has no entry until they do.
  const allDrivers = [...new Set(data.flatMap((row) => Object.keys(row)))].filter(
    (key) => key !== xKey,
  );
  const highlighted = new Set(highlightDrivers);
  const maxPosition = allDrivers.length || 1;

  return (
    <ResponsiveContainer width="100%" height={420}>
      <LineChart data={data} margin={{ left: 10, right: 20, top: 10, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
        <XAxis
          type="number"
          dataKey={xKey}
          domain={["dataMin", "dataMax"]}
          allowDecimals={false}
          tick={{ fill: COLORS.textSecondary, fontSize: 12 }}
          label={{ value: xLabel, position: "insideBottom", offset: -8, fill: COLORS.textSecondary }}
        />
        <YAxis
          type="number"
          domain={[1, maxPosition]}
          reversed
          allowDecimals={false}
          tick={{ fill: COLORS.textSecondary, fontSize: 12 }}
          label={{ value: yLabel, angle: -90, position: "insideLeft", fill: COLORS.textSecondary }}
        />
        <Tooltip content={<PositionTooltip describeX={describeX} />} />
        <Legend
          payload={highlightDrivers.map((driver, i) => ({
            value: driver,
            type: "line",
            color: COLORS.categorical[i % COLORS.categorical.length],
          }))}
          // Clear of the x-axis label, which sits below the axis.
          wrapperStyle={{ color: COLORS.text, paddingTop: 16 }}
        />
        {allDrivers.map((driver) => {
          const isHighlighted = highlighted.has(driver);
          const index = highlightDrivers.indexOf(driver);
          return (
            <Line
              key={driver}
              dataKey={driver}
              name={driver}
              stroke={isHighlighted ? COLORS.categorical[index % COLORS.categorical.length] : MUTED_STROKE}
              strokeWidth={isHighlighted ? 2 : 1}
              strokeOpacity={isHighlighted ? 1 : 0.55}
              dot={false}
              isAnimationActive={false}
              connectNulls
            />
          );
        })}
      </LineChart>
    </ResponsiveContainer>
  );
}
