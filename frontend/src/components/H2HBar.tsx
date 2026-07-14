import { COLORS } from "../theme/theme";

interface Props {
  leftName: string;
  leftCode: string;
  leftWins: number;
  rightName: string;
  rightCode: string;
  rightWins: number;
}

export default function H2HBar({
  leftName,
  leftCode,
  leftWins,
  rightName,
  rightCode,
  rightWins,
}: Props) {
  const total = leftWins + rightWins;
  const leftPct = total > 0 ? (leftWins / total) * 100 : 50;

  return (
    <div className="h2h-bar">
      <div className="h2h-bar-labels">
        <span>
          {leftName} ({leftCode}) — {leftWins}
        </span>
        <span>
          {rightWins} — {rightName} ({rightCode})
        </span>
      </div>
      <div className="h2h-bar-track">
        <div
          className="h2h-bar-fill"
          style={{ width: `${leftPct}%`, background: COLORS.categorical[0] }}
        />
        <div
          className="h2h-bar-fill"
          style={{ width: `${100 - leftPct}%`, background: COLORS.categorical[1] }}
        />
      </div>
    </div>
  );
}
