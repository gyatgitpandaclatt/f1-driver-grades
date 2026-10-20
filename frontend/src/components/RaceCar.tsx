import type { Era } from "../theme/eras";

interface Shape {
  body: string;
  detail: string;
  wing: string;
  // Wing elements that move: drawn apart so the 2026 car's active aero can flap.
  flaps?: string;
  wheels: [number, number, number, number];
  halo?: boolean;
  bigRims?: boolean;
}

// A side-on silhouette of each era's car, nose to the right. Livery comes
// from the era's --car-* custom properties, so this only draws the shapes.
const SHAPES: Record<Era["id"], Shape> = {
  // ~2004: tall airbox, high narrow nose, short sidepods, small rims on tall grooved tyres.
  refuelling: {
    body: "M30 60 L30 47 L68 45 L92 30 L110 25 L122 27 L131 40 L152 42 L178 44 L238 50 L264 56 L266 60 Z",
    detail: "M84 60 L90 50 L148 49 L160 60 Z",
    wing: "M12 18 H19 V56 H12 Z M19 21 H44 V28 H19 Z M19 32 H40 V37 H19 Z M240 61 H288 V66 H240 Z M282 52 H289 V66 H282 Z",
    wheels: [56, 13, 222, 12],
  },
  // ~2014: low stepped "finger" nose, shark-fin engine cover, longer wheelbase.
  drs: {
    body: "M28 60 L28 46 L58 44 L96 28 L112 26 L124 30 L134 42 L184 46 L246 55 L280 58 L282 61 Z",
    detail: "M40 44 L96 28 L98 44 Z",
    wing: "M10 22 H17 V56 H10 Z M17 24 H44 V30 H17 Z M17 34 H38 V38 H17 Z M244 62 H294 V66 H244 Z M288 54 H295 V66 H288 Z",
    wheels: [56, 12, 230, 12],
  },
  // ~2022: long and low, sculpted floor, halo over the cockpit, 18-inch rims.
  "ground-effect": {
    body: "M26 58 L26 45 L60 43 L98 29 L114 28 L126 33 L138 44 L190 47 L250 54 L284 58 L286 61 L26 61 Z",
    detail: "M80 61 Q120 50 176 52 L190 61 Z",
    wing: "M8 20 H16 V58 H8 Z M16 22 Q32 18 46 24 V30 H16 Z M16 40 H34 V44 H16 Z M246 62 Q270 58 296 62 V66 H246 Z M290 52 H297 V66 H290 Z",
    wheels: [56, 16, 236, 16],
    halo: true,
    bigRims: true,
  },
  // 2026: shorter and narrower, no beam wing, front and rear wing flaps that move.
  hybrid: {
    body: "M30 58 L30 45 L62 43 L98 30 L114 28 L126 33 L138 44 L186 47 L240 54 L272 58 L274 61 L30 61 Z",
    detail: "M84 61 Q118 51 168 53 L180 61 Z",
    wing: "M12 20 H20 V58 H12 Z M236 62 Q258 58 282 62 V66 H236 Z M276 52 H283 V66 H276 Z",
    flaps: "M20 22 H46 V28 H20 Z M240 56 H272 V59 H240 Z",
    wheels: [62, 15, 226, 15],
    halo: true,
    bigRims: true,
  },
};

function Wheel({ cx, r, rim }: { cx: number; r: number; rim: number }) {
  return (
    <g>
      <circle cx={cx} cy={78 - r} r={r} fill="var(--car-tyre)" />
      <circle cx={cx} cy={78 - r} r={rim} fill="var(--car-rim)" />
      {/* The spokes spin; the tyre and rim don't need to. */}
      <g className="wheel-spokes">
        <path
          d={`M${cx - rim} ${78 - r} H${cx + rim} M${cx} ${78 - r - rim} V${78 - r + rim}`}
          stroke="var(--car-tyre)"
          strokeWidth={1.6}
        />
      </g>
    </g>
  );
}

export default function RaceCar({ era }: { era: Era["id"] }) {
  const { body, detail, wing, flaps, wheels, halo, bigRims } = SHAPES[era];
  const [rearX, rearR, frontX, frontR] = wheels;
  // 13-inch rims on tall tyres until 2022, then 18-inch on low profiles.
  const rimRatio = bigRims ? 0.7 : 0.5;
  return (
    <svg className="race-car" viewBox="0 0 300 80" aria-hidden="true">
      <path d={wing} fill="var(--car-trim)" />
      {flaps && <path className="aero-flaps" d={flaps} fill="var(--car-trim)" />}
      <path d={body} fill="var(--car-body)" />
      <path d={detail} fill="var(--car-trim)" opacity={0.85} />
      <circle cx={halo ? 126 : 122} cy={era === "refuelling" ? 33 : 35} r={6} fill="var(--car-helmet)" />
      {halo && <path d="M110 32 Q127 20 144 36" fill="none" stroke="var(--car-trim)" strokeWidth={3} />}
      <Wheel cx={rearX} r={rearR} rim={rearR * rimRatio} />
      <Wheel cx={frontX} r={frontR} rim={frontR * rimRatio} />
    </svg>
  );
}
