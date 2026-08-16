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
}: {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
  label?: number;
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
      <div style={{ color: COLORS.text, fontWeight: 600, marginBottom: 4 }}>Lap {label}</div>
      {rows.map((p) => (
        <div key={p.dataKey} style={{ color: COLORS.textSecondary, fontSize: 12 }}>
          P{p.value} — <span style={{ color: p.color }}>{p.dataKey}</span>
        </div>
      ))}
    </div>
  );
}

export default function PositionChangesChart({ data, highlightDrivers }: Props) {
  const allDrivers = Object.keys(data[0] ?? {}).filter((key) => key !== "lap");
  const highlighted = new Set(highlightDrivers);
  const maxPosition = allDrivers.length || 1;

  return (
    <ResponsiveContainer width="100%" height={420}>
      <LineChart data={data} margin={{ left: 10, right: 20, top: 10, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
        <XAxis
          type="number"
          dataKey="lap"
          domain={["dataMin", "dataMax"]}
          tick={{ fill: COLORS.textSecondary, fontSize: 12 }}
          label={{ value: "Lap", position: "insideBottom", offset: -8, fill: COLORS.textSecondary }}
        />
        <YAxis
          type="number"
          domain={[1, maxPosition]}
          reversed
          allowDecimals={false}
          tick={{ fill: COLORS.textSecondary, fontSize: 12 }}
          label={{ value: "Position", angle: -90, position: "insideLeft", fill: COLORS.textSecondary }}
        />
        <Tooltip content={<PositionTooltip />} />
        <Legend
          payload={highlightDrivers.map((driver, i) => ({
            value: driver,
            type: "line",
            color: COLORS.categorical[i % COLORS.categorical.length],
          }))}
          wrapperStyle={{ color: COLORS.text }}
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
