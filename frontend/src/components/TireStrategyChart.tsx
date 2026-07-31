import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Stint } from "../api/types";
import { COLORS, COMPOUND_COLORS } from "../theme/theme";

interface Props {
  stints: Stint[];
  driverOrder: string[]; // top-to-bottom row order (e.g. finishing order)
  totalLaps: number;
}

interface StintRow {
  driver: string;
  [key: string]: string | number;
}

function TireTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { payload: StintRow }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  const rowStints: { compound: string; length: number }[] = [];
  Object.keys(row).forEach((key) => {
    if (!key.startsWith("length_")) return;
    const i = key.slice("length_".length);
    const length = row[key] as number;
    const compound = row[`compound_${i}`] as string;
    if (length > 0 && compound) rowStints.push({ compound, length });
  });

  return (
    <div
      style={{
        background: COLORS.surface,
        border: `1px solid ${COLORS.border}`,
        borderRadius: 4,
        padding: 8,
      }}
    >
      <div style={{ color: COLORS.text, fontWeight: 600, marginBottom: 4 }}>{label}</div>
      {rowStints.map((s, i) => (
        <div key={i} style={{ color: COLORS.textSecondary, fontSize: 12 }}>
          <span style={{ color: COMPOUND_COLORS[s.compound] ?? COMPOUND_COLORS.UNKNOWN }}>{"● "}</span>
          {s.compound} — {s.length} lap{s.length === 1 ? "" : "s"}
        </div>
      ))}
    </div>
  );
}

export default function TireStrategyChart({ stints, driverOrder, totalLaps }: Props) {
  const byDriver = new Map<string, Stint[]>();
  for (const s of stints) {
    const list = byDriver.get(s.driver) ?? [];
    list.push(s);
    byDriver.set(s.driver, list);
  }
  for (const list of byDriver.values()) {
    list.sort((a, b) => a.lap_start - b.lap_start);
  }

  const maxStints = Math.max(1, ...Array.from(byDriver.values(), (list) => list.length));
  const usedCompounds = Array.from(new Set(stints.map((s) => s.compound)));

  const rows: StintRow[] = driverOrder.map((driver) => {
    const driverStints = byDriver.get(driver) ?? [];
    const row: StintRow = { driver };
    for (let i = 0; i < maxStints; i++) {
      const stint = driverStints[i];
      row[`length_${i}`] = stint ? stint.lap_end - stint.lap_start + 1 : 0;
      row[`compound_${i}`] = stint ? stint.compound : "";
    }
    return row;
  });

  const height = Math.max(240, rows.length * 28 + 70);

  return (
    <div>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={rows} layout="vertical" margin={{ left: 10, right: 20, top: 10, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} horizontal={false} />
          <XAxis
            type="number"
            domain={[0, totalLaps]}
            tick={{ fill: COLORS.textSecondary, fontSize: 12 }}
            label={{ value: "Lap", position: "insideBottom", offset: -8, fill: COLORS.textSecondary }}
          />
          <YAxis type="category" dataKey="driver" width={50} tick={{ fill: COLORS.text, fontSize: 12 }} />
          <Tooltip content={<TireTooltip />} cursor={{ fill: COLORS.surface2 }} />
          {Array.from({ length: maxStints }, (_, i) => (
            <Bar key={i} dataKey={`length_${i}`} stackId="stints" isAnimationActive={false}>
              {rows.map((row, rowIdx) => (
                <Cell
                  key={rowIdx}
                  fill={COMPOUND_COLORS[(row[`compound_${i}`] as string) || "UNKNOWN"] ?? COMPOUND_COLORS.UNKNOWN}
                  stroke={COLORS.background}
                  strokeWidth={1}
                />
              ))}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", fontSize: 12, color: COLORS.textSecondary }}>
        {usedCompounds.map((compound) => (
          <div key={compound} style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span
              style={{
                display: "inline-block",
                width: 10,
                height: 10,
                borderRadius: 2,
                background: COMPOUND_COLORS[compound] ?? COMPOUND_COLORS.UNKNOWN,
              }}
            />
            {compound}
          </div>
        ))}
      </div>
    </div>
  );
}
