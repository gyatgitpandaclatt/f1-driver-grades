import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { COLORS } from "../theme/theme";

export interface DriverBarDatum {
  code: string;
  name: string;
  value: number;
}

interface Props {
  data: DriverBarDatum[];
  neutral?: number;
  domain?: [number, number];
}

export default function DriverBarChart({ data, neutral = 50, domain = [0, 100] }: Props) {
  const sorted = [...data].sort((a, b) => b.value - a.value);
  const height = Math.max(280, sorted.length * 26);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={sorted} layout="vertical" margin={{ left: 10, right: 30 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#38383e" horizontal={false} />
        <XAxis
          type="number"
          domain={domain}
          tick={{ fill: COLORS.textSecondary, fontSize: 12 }}
        />
        <YAxis
          type="category"
          dataKey="code"
          width={50}
          tick={{ fill: COLORS.text, fontSize: 12 }}
        />
        <ReferenceLine x={neutral} stroke={COLORS.textSecondary} strokeDasharray="3 3" />
        <Tooltip
          formatter={(value: number) => value.toFixed(1)}
          labelFormatter={(_, payload) => payload?.[0]?.payload?.name ?? ""}
          contentStyle={{ background: COLORS.surface, border: "1px solid #38383e" }}
          labelStyle={{ color: COLORS.text }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {sorted.map((d) => (
            <Cell key={d.code} fill={d.value >= neutral ? COLORS.correct : COLORS.incorrect} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
