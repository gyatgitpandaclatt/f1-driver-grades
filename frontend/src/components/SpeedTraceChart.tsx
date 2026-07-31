import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SpeedTracePoint } from "../api/types";
import { COLORS } from "../theme/theme";

interface Props {
  data: Record<string, SpeedTracePoint[]>;
}

export default function SpeedTraceChart({ data }: Props) {
  const drivers = Object.keys(data).slice(0, 3);
  const maxDistance = Math.max(1, ...drivers.flatMap((d) => data[d].map((p) => p.distance)));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <LineChart margin={{ left: 10, right: 20, top: 10, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
        <XAxis
          type="number"
          dataKey="distance"
          domain={[0, maxDistance]}
          tick={{ fill: COLORS.textSecondary, fontSize: 12 }}
          label={{ value: "Distance (m)", position: "insideBottom", offset: -8, fill: COLORS.textSecondary }}
        />
        <YAxis
          type="number"
          dataKey="speed"
          tick={{ fill: COLORS.textSecondary, fontSize: 12 }}
          label={{ value: "Speed (km/h)", angle: -90, position: "insideLeft", fill: COLORS.textSecondary }}
        />
        <Tooltip
          contentStyle={{ background: COLORS.surface, border: `1px solid ${COLORS.border}` }}
          labelStyle={{ color: COLORS.text }}
          itemStyle={{ color: COLORS.text }}
          formatter={(value: number) => `${value.toFixed(0)} km/h`}
          labelFormatter={(value: number) => `${value.toFixed(0)} m`}
        />
        <Legend wrapperStyle={{ color: COLORS.text }} />
        {drivers.map((driver, i) => (
          <Line
            key={driver}
            data={data[driver]}
            dataKey="speed"
            name={driver}
            stroke={COLORS.categorical[i % COLORS.categorical.length]}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
