import { motion } from "framer-motion";
import type { Era } from "../theme/eras";
import RaceCar from "./RaceCar";

const LIGHTS = 5;
const LIGHT_STEP = 0.25; // seconds between lights, as on a real gantry
const LIGHTS_OUT = 0.2 + LIGHTS * LIGHT_STEP + 0.35;

// The era's banner: five start lights come on one by one and go out, then
// the era's car launches onto a track that keeps scrolling under it. Keyed on
// the season by the caller, so every season pick runs the start again.
export default function EraHero({ era, season }: { era: Era; season: number | null }) {
  return (
    <section className="era-hero" aria-label={`${era.name}, ${era.years}`}>
      <div className="era-copy">
        <div className="era-kicker">
          <span className="era-years">{era.years}</span>
          {season != null && <span className="era-season">Season {season}</span>}
        </div>
        <h2 className="era-name">{era.name}</h2>
        <p className="era-tagline">{era.tagline}</p>
        {/* 2026's energy store and the modes that spend it, cycling in turn. */}
        {era.id === "hybrid" && (
          <div className="ers-hud" aria-hidden="true">
            <span className="ers-label">ERS</span>
            <span className="ers-bar"><i /></span>
            <span className="ers-mode">Straight Mode</span>
            <span className="ers-mode">Overtake</span>
            <span className="ers-mode">Boost</span>
          </div>
        )}
      </div>

      <div className="start-lights" aria-hidden="true">
        {Array.from({ length: LIGHTS }, (_, i) => {
          const on = (0.2 + i * LIGHT_STEP) / LIGHTS_OUT;
          return (
            <span key={i} className="start-light">
              <motion.i
                initial={{ opacity: 0.12 }}
                animate={{ opacity: [0.12, 0.12, 1, 1, 0.12] }}
                transition={{ duration: LIGHTS_OUT + 0.1, times: [0, on, on + 0.01, 0.97, 1], ease: "linear" }}
              />
            </span>
          );
        })}
      </div>

      <div className="era-track" aria-hidden="true">
        <div className="track-scroll" />
        <motion.div
          className="car-slot"
          initial={{ x: "-90vw" }}
          animate={{ x: 0 }}
          transition={{ delay: LIGHTS_OUT, type: "spring", stiffness: 70, damping: 16 }}
        >
          <RaceCar era={era.id} />
        </motion.div>
      </div>
    </section>
  );
}
