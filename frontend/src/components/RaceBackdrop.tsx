import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import type { Era } from "../theme/eras";

// Streaks of a car going by, behind everything. Fixed positions and timings
// (not random) so a re-render doesn't reshuffle them.
const STREAKS = Array.from({ length: 12 }, (_, i) => ({
  top: `${(i * 37) % 100}%`,
  width: `${18 + ((i * 13) % 22)}vw`,
  animationDuration: `${2.4 + ((i * 7) % 10) / 4}s`,
  animationDelay: `${-((i * 11) % 17) / 3}s`,
}));

export default function RaceBackdrop({ era }: { era: Era["id"] }) {
  // A chequered flag sweeps across when the era changes, not on first load.
  const previous = useRef(era);
  const [wipes, setWipes] = useState(0);
  useEffect(() => {
    if (previous.current !== era) {
      previous.current = era;
      setWipes((n) => n + 1);
    }
  }, [era]);

  return (
    <>
      <div className="race-backdrop" aria-hidden="true">
        <div className="backdrop-texture" />
        <div className="backdrop-floor" />
        {STREAKS.map((style, i) => (
          <span key={i} className="speed-streak" style={style} />
        ))}
      </div>
      {/* Outside the backdrop: that sits behind the page, the flag goes over it. */}
      {wipes > 0 && (
        <motion.div
          key={wipes}
          className="era-wipe"
          aria-hidden="true"
          initial={{ x: "-110%" }}
          animate={{ x: "110%" }}
          transition={{ duration: 0.9, ease: [0.7, 0, 0.3, 1] }}
        />
      )}
    </>
  );
}
