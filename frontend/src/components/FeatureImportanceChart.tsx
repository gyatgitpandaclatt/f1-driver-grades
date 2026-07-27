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
import type { FeatureImportance, RfMetrics } from "../api/types";
import { COLORS } from "../theme/theme";

const FEATURE_LABELS: Record<string, string> = {
  avg_finish_minus_grid: "Avg finish vs grid",
  overperf_share: "Overperformance share",
  underperf_share: "Underperformance share",
  is_rookie: "Rookie",
};

function pct(value: number): string {
  return `${(value * 100).toFixed(0)}%`;
}

export default function FeatureImportanceChart({
  data,
  note,
  rfMetrics,
}: {
  data: FeatureImportance[] | null;
  note: string | null;
  rfMetrics: RfMetrics | null;
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

  const chartData = data
    .filter((d) => d.feature !== "races")
    .map((d) => ({
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

      {rfMetrics && (
        <>
          <p className="model-note">RF performance (leave-one-out CV):</p>
          <div className="stat-grid">
            <div className="stat-tile">
              <div className="stat-value">{pct(rfMetrics.accuracy)}</div>
              <div className="stat-label">Accuracy</div>
            </div>
            <div className="stat-tile">
              <div className="stat-value">{pct(rfMetrics.macro_precision)}</div>
              <div className="stat-label">Macro precision</div>
            </div>
            <div className="stat-tile">
              <div className="stat-value">{pct(rfMetrics.macro_recall)}</div>
              <div className="stat-label">Macro recall</div>
            </div>
            <div className="stat-tile">
              <div className="stat-value">{pct(rfMetrics.macro_f1)}</div>
              <div className="stat-label">Macro F1</div>
            </div>
          </div>
          <ul className="misclassified-list">
            {rfMetrics.per_class.map((c) => (
              <li key={c.label}>
                <strong>{c.label}</strong> — precision {pct(c.precision)}, recall{" "}
                {pct(c.recall)}, F1 {pct(c.f1)} (n={c.support})
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
