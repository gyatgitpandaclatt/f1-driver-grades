// Recharts needs literal color strings (not CSS vars) for fill/stroke props.
// Keep these in sync with the CSS custom properties in src/index.css.
export const COLORS = {
  background: "#0a0a0c",
  surface: "#111116",
  surface2: "#18181f",
  text: "#f0f0f5",
  textSecondary: "#7878a0",
  border: "#22222e",
  accent: "#e10600",
  categorical: ["#4db8ff", "#00d68f", "#ffb347", "#ff6b6b", "#c084fc"],
  correct: "#00d68f",
  incorrect: "#ffd400",
} as const;

export const GRADE_COLORS: Record<string, string> = {
  S: "#00d68f",   // bright green — elite
  A: "#4db8ff",   // bright blue — strong
  B: "#ffb347",   // amber — solid
  C: "#ff6b6b",   // red-pink — below par
  D: "#c084fc",   // purple — poor
};

export const GRADE_ORDER: Record<string, number> = {
  S: 5,
  A: 4,
  B: 3,
  C: 2,
  D: 1,
};

export const LABEL_Y: Record<string, number> = {
  underperformer: 0,
  expected: 1,
  overperformer: 2,
};

export const Y_LABEL_ORDER = ["underperformer", "expected", "overperformer"];
