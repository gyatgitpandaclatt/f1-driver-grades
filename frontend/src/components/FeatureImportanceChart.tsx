import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { FeatureImportance } from "../api/types";
import { COLORS } from "../theme/theme";

const FEATURE_LABELS: Record<string, string> = {
  races: "Races entered",
  avg_finish_minus_grid: "Avg finish vs grid",
  overperf_share: "Overperformance share",
  underperf_share: "Underperformance share",
  is_rookie: "Rookie",
};

export default function FeatureImportanceChart({
  data,
  note,
}: {
  data: FeatureImportance[] | null;
  note: string | null;
}) {
  if (!data) {
    return (
      <div className="panel">
        <h2>Feature Importances</h2>
        <p className="model-note">
          {note ?? "Model has not run yet — not enough data."}
        </p>
      </div>
    );
  }

  const chartData = data.map((d) => ({
    feature: FEATURE_LABELS[d.feature] ?? d.feature,
    importance: d.importance,
  }));

  return (
    <div className="panel">
      <h2>RF Feature Importances</h2>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#38383e" horizontal={false} />
          <XAxis type="number" tick={{ fill: COLORS.textSecondary, fontSize: 12 }} />
          <YAxis
            type="category"
            dataKey="feature"
            width={150}
            tick={{ fill: COLORS.text, fontSize: 12 }}
          />
          <Tooltip
            formatter={(value: number) => value.toFixed(3)}
            contentStyle={{ background: COLORS.surface, border: "1px solid #38383e" }}
            labelStyle={{ color: COLORS.text }}
          />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS.categorical[i % COLORS.categorical.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
