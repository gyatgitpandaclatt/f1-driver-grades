import { motion } from "framer-motion";
import { NavLink } from "react-router-dom";

const LINKS = [
  { to: "/", label: "Driver Grades", end: true },
  { to: "/qualifying-h2h", label: "Qualifying H2H" },
  { to: "/overperformance", label: "Overperformance" },
  { to: "/grid-improvement", label: "Grid Improvement" },
  { to: "/methodology", label: "Methodology" },
];

export default function Nav() {
  return (
    <nav className="nav">
      {LINKS.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
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
    </nav>
  );
}
