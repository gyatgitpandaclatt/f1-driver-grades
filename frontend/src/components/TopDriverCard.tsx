import type { CSSProperties } from "react";
import type { DriverGrade } from "../api/types";
import { eraFor } from "../theme/eras";
import { teamColor } from "../theme/teams";
import { splitName } from "./DriverTable";

// Camera flashes from the photographers' pit (DRS and hybrid eras), fixed
// spots and timings so a re-render doesn't move them.
const FLASHES = Array.from({ length: 9 }, (_, i) => ({
  left: `${8 + ((i * 37) % 84)}%`,
  top: `${10 + ((i * 53) % 70)}%`,
  animationDelay: `${((i * 7) % 11) * 0.37}s`,
}));

// Champagne off the top step (refuelling era): droplets thrown up and out.
const DROPLETS = Array.from({ length: 16 }, (_, i) => ({
  "--dx": `${40 + ((i * 29) % 120)}px`,
  "--dy": `${-30 - ((i * 17) % 70)}px`,
  animationDelay: `${(i % 8) * 0.18}s`,
})) as CSSProperties[];

// Laurel leaves round the grade, as on the 2025 world champion board.
function Laurel() {
  const leaves = Array.from({ length: 6 }, (_, i) => {
    const a = (118 + i * 18) * (Math.PI / 180);
    const x = 50 + Math.cos(a) * 40;
    const y = 52 + Math.sin(a) * 40;
    const rot = (a * 180) / Math.PI + 90;
    return { x, y, rot };
  });
  return (
    <svg className="laurel" viewBox="0 0 100 100" aria-hidden="true">
      {[1, -1].map((side) => (
        <g key={side} transform={side === -1 ? "translate(100 0) scale(-1 1)" : undefined}>
          {leaves.map(({ x, y, rot }, i) => (
            <ellipse key={i} cx={x} cy={y} rx={4} ry={9} transform={`rotate(${rot} ${x} ${y})`} />
          ))}
        </g>
      ))}
    </svg>
  );
}

// The season's top grade, set like a driver's name on a team's banner: first
// name in script, surname huge. Each era dresses it as its own photos did.
export default function TopDriverCard({ drivers, season }: { drivers: DriverGrade[]; season: number }) {
  if (drivers.length === 0) return null;
  const top = drivers.reduce((a, b) => (b.composite > a.composite ? b : a));
  const [first, surname] = splitName(top.driver_name);
  const era = eraFor(season);
  return (
    <section
      className={`top-card top-${era.id}`}
      style={{ "--team": teamColor(top.constructor, season) } as CSSProperties}
      aria-label={`Top grade of ${season}: ${top.driver_name}, ${top.grade}, ${top.composite.toFixed(1)}`}
    >
      <div className="top-backdrop" aria-hidden="true" />
      <div className="top-copy">
        <span className="top-kicker">Top grade · {season}</span>
        <span className="top-first">{first}</span>
        <span className="top-surname">{surname}</span>
        <span className="top-team">
          <i className="team-dot" aria-hidden="true" />
          {top.constructor}
        </span>
      </div>
      <div className="top-board" aria-hidden="true">
        {era.id === "ground-effect" && <Laurel />}
        <span className="board-line">
          P{top.position_text === String(top.position) ? top.position : top.position_text}
        </span>
        <span className="board-grade">{top.grade}</span>
        <span className="board-line">{top.composite.toFixed(1)}</span>
      </div>
      <div className="top-effects" aria-hidden="true">
        {(era.id === "drs" || era.id === "hybrid") &&
          FLASHES.map((style, i) => <i key={i} className="flash" style={style} />)}
        {era.id === "refuelling" && DROPLETS.map((style, i) => <i key={i} className="droplet" style={style} />)}
        {era.id === "ground-effect" &&
          [0, 1, 2].map((i) => <i key={i} className={`firework fw-${i}`} />)}
      </div>
    </section>
  );
}
