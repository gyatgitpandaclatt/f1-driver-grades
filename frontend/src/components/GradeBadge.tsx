import { GRADE_COLORS } from "../theme/theme";

export default function GradeBadge({ grade }: { grade: string }) {
  const color = GRADE_COLORS[grade] ?? "#909094";
  return (
    <span className="grade-badge" style={{ backgroundColor: color }}>
      {grade}
    </span>
  );
}
