import { GRADE_COLORS } from "../theme/theme";

export default function GradeBadge({ grade }: { grade: string }) {
  const color = GRADE_COLORS[grade] ?? "#7878a0";
  return (
    <span className="grade-badge" style={{ backgroundColor: color }}>
      {grade}
    </span>
  );
}
