import { motion } from "framer-motion";
import { NavLink, useLocation } from "react-router";
import SeasonSelector from "./SeasonSelector";

interface Props {
  isPastSeason: boolean;
  seasons: number[];
  currentSeason: number | null;
  selectedSeason: number | null;
}

export default function Nav({ isPastSeason, seasons, currentSeason, selectedSeason }: Props) {
  // Keep ?season= across tabs: switching tab must not switch season.
  const { search } = useLocation();
  const links = [
    { to: "/", label: "Driver Grades", end: true },
    { to: "/qualifying-h2h", label: "Qualifying H2H" },
    { to: "/overperformance", label: "Overperformance" },
    { to: "/grid-improvement", label: "Grid Improvement" },
    // A finished season has no "latest race" left to summarise; the
    // current one isn't over, so it has no season summary yet.
    isPastSeason
      ? { to: "/season-summary", label: "Season Summary" }
      : { to: "/race-summary", label: "Race Summary" },
    { to: "/methodology", label: "Methodology" },
  ];

  return (
    <nav className="nav">
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={{ pathname: link.to, search }}
          end={link.end}
          className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
        >
          {({ isActive }) => (
            <>
              {link.label}
              {isActive && (
                <motion.div
                  className="nav-underline"
                  layoutId="nav-underline"
                  transition={{ type: "spring", stiffness: 500, damping: 40 }}
                />
              )}
            </>
          )}
        </NavLink>
      ))}
      <SeasonSelector
        seasons={seasons}
        currentSeason={currentSeason}
        selectedSeason={selectedSeason}
      />
    </nav>
  );
}
