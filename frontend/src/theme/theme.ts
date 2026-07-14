// Recharts needs literal color strings (not CSS vars) for fill/stroke props.
// Keep these in sync with the CSS custom properties in src/index.css.
export const COLORS = {
  background: "#1D1D20",
  surface: "#26262B",
  text: "#fbfbff",
  textSecondary: "#909094",
  categorical: ["#A1C9F4", "#FFB482", "#8DE5A1", "#FF9F9B", "#D0BBFF"],
  correct: "#17b26a",
  incorrect: "#ffd400",
} as const;

export const GRADE_COLORS: Record<string, string> = {
  S: "#8DE5A1",
  A: "#A1C9F4",
  B: "#FFB482",
  C: "#FF9F9B",
  D: "#D0BBFF",
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
