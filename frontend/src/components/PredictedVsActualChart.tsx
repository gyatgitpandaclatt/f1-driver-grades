import { useState } from "react";
import type { PredictedVsActualPoint } from "../api/types";
import { COLORS, LABEL_Y, Y_LABEL_ORDER } from "../theme/theme";

// Recharts' <Customized> escape hatch for a per-category connecting line +
// two marker shapes turned out to depend on internal xAxisMap/yAxisMap
// scale shapes that aren't practical to verify without a live browser
// render available in this environment. A small hand-rolled SVG component
// gives the same interactive result (hover tooltip, connecting line, two
// marker shapes, conditional color) with behavior that's fully inspectable
// as plain code — an accepted substitution per the design (interactivity
// is the requirement, not the specific charting library).

const COLUMN_WIDTH = 44;
const LEFT_PADDING = 90;
const RIGHT_PADDING = 20;
const TOP_PADDING = 20;
const BOTTOM_PADDING = 40;
const ROW_HEIGHT = 70;
const CHART_HEIGHT = TOP_PADDING + BOTTOM_PADDING + ROW_HEIGHT * 2;

function yForValue(value: number): number {
  // value 2 (overperformer) at top, 0 (underperformer) at bottom
  return TOP_PADDING + (2 - value) * ROW_HEIGHT;
}

export default function PredictedVsActualChart({ data }: { data: PredictedVsActualPoint[] }) {
  const [hovered, setHovered] = useState<number | null>(null);

  if (data.length === 0) {
    return (
      <div className="panel">
        <h2>Predicted vs Actual Season Label</h2>
        <p className="model-note">No predictions available yet.</p>
      </div>
    );
  }

  const width = LEFT_PADDING + RIGHT_PADDING + COLUMN_WIDTH * data.length;
  const hoveredPoint = hovered != null ? data[hovered] : null;

  return (
    <div className="panel">
      <h2>Predicted vs Actual Season Label</h2>
      <div style={{ overflowX: "auto" }}>
        <svg width={width} height={CHART_HEIGHT} role="img">
          {Y_LABEL_ORDER.map((label) => {
            const y = yForValue(LABEL_Y[label]);
            return (
              <g key={label}>
                <line
                  x1={LEFT_PADDING}
                  x2={width - RIGHT_PADDING}
                  y1={y}
                  y2={y}
                  stroke="#38383e"
                  strokeDasharray="3 3"
                />
                <text x={8} y={y + 4} fill={COLORS.text} fontSize={11}>
                  {label}
                </text>
              </g>
            );
          })}

          {data.map((row, i) => {
            const x = LEFT_PADDING + COLUMN_WIDTH * i + COLUMN_WIDTH / 2;
            const actualY = yForValue(LABEL_Y[row.actual_label] ?? 1);
            const predictedY = yForValue(LABEL_Y[row.predicted_label] ?? 1);
            const predictedColor = row.correct ? COLORS.correct : COLORS.incorrect;
            const diamondSize = 6;

            return (
              <g
                key={row.driver_code}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
                style={{ cursor: "pointer" }}
              >
                <line x1={x} x2={x} y1={actualY} y2={predictedY} stroke="#555" strokeWidth={1.2} />
                <circle cx={x} cy={actualY} r={5} fill={COLORS.textSecondary} />
                <polygon
                  points={`${x},${predictedY - diamondSize} ${x + diamondSize},${predictedY} ${x},${predictedY + diamondSize} ${x - diamondSize},${predictedY}`}
                  fill={predictedColor}
                />
                <text
                  x={x}
                  y={CHART_HEIGHT - BOTTOM_PADDING + 16}
                  fill={COLORS.textSecondary}
                  fontSize={10}
                  textAnchor="end"
                  transform={`rotate(-45 ${x} ${CHART_HEIGHT - BOTTOM_PADDING + 16})`}
                >
                  {row.driver_code}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {hoveredPoint && (
        <div className="model-note">
          <strong>{hoveredPoint.driver_code}</strong> — actual: {hoveredPoint.actual_label}, predicted:{" "}
          {hoveredPoint.predicted_label} ({hoveredPoint.correct ? "correct" : "incorrect"})
        </div>
      )}

      <div className="chart-legend">
        <span>
          <span className="swatch" style={{ background: COLORS.textSecondary }} />
          Actual
        </span>
        <span>
          <span className="swatch" style={{ background: COLORS.correct }} />
          Predicted (correct)
        </span>
        <span>
          <span className="swatch" style={{ background: COLORS.incorrect }} />
          Predicted (wrong)
        </span>
      </div>
    </div>
  );
}
