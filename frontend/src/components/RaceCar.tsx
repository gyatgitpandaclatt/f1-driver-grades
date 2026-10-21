import type { ReactNode } from "react";
import type { Era } from "../theme/eras";

// Side-on drawings of each era's car, nose to the right, ground at y=96 (one
// unit is about 1.5 cm). Paint comes from classes styled by the era's --car-*
// properties in index.css: .cb body, .ct trim, .cf carbon, .ch helmet.

interface WheelProps {
  cx: number;
  r: number;
  rim: number;
  // A coloured Pirelli compound stripe on the sidewall (2011 on).
  band?: boolean;
  // A wheel cover over the rim (2022 on) in place of open spokes.
  cover?: boolean;
}

function Wheel({ cx, r, rim, band, cover }: WheelProps) {
  const cy = 96 - r;
  const marks = cover ? 3 : 5;
  return (
    <g>
      <circle className="tyre" cx={cx} cy={cy} r={r} />
      {band && <circle className="tyre-band" cx={cx} cy={cy} r={rim + (r - rim) * 0.45} />}
      <circle className={cover ? "wheel-cover" : "rim"} cx={cx} cy={cy} r={rim} />
      {/* What turns: spokes, or the marks on a cover. The clear circle keeps
          the group's box centred on the hub so it spins in place. */}
      <g className="wheel-spokes">
        <circle cx={cx} cy={cy} r={rim} fill="none" />
        {Array.from({ length: marks }, (_, i) => {
          const a = (i / marks) * Math.PI * 2;
          const inner = cover ? rim * 0.55 : rim * 0.3;
          const outer = cover ? rim * 0.85 : rim * 0.95;
          return (
            <line
              key={i}
              className={cover ? "cover-mark" : "spoke"}
              x1={cx + Math.cos(a) * inner}
              y1={cy + Math.sin(a) * inner}
              x2={cx + Math.cos(a) * outer}
              y2={cy + Math.sin(a) * outer}
            />
          );
        })}
      </g>
      <circle className="hub" cx={cx} cy={cy} r={rim * 0.22} />
    </g>
  );
}

// The driver's helmet, sitting low in the cockpit, visor forward.
function Helmet({ cx }: { cx: number }) {
  const cy = 42;
  return (
    <g>
      <circle className="ch" cx={cx} cy={cy} r={7} />
      <path className="visor" d={`M${cx + 1} ${cy - 3.5} H${cx + 6} Q${cx + 7.6} ${cy - 1.5} ${cx + 6.4} ${cy + 0.8} H${cx + 1} Z`} />
    </g>
  );
}

// ~2000-2004 (F1-2000): tall airbox, high nose over a low front wing on
// pylons, short sidepods, a tall rear-wing endplate, small rims on tall tyres.
function Refuelling() {
  return (
    <>
      <path className="cf" d="M48 88 H292 V91 H48 Z" />
      <Helmet cx={210} />
      <path className="cb" d="M36 72 L46 64 L92 58 L150 46 L170 32 L188 30 L192 40 L198 46 L232 47 L242 50 L264 54 L300 65 L314 72 Q318 76 312 78 L300 77 L262 70 L246 72 L240 88 L48 88 L38 80 Z" />
      <path className="cf" d="M186 31 L191 31 L194 40 L189 40 Z" />
      <path className="cb" d="M112 88 L116 62 Q118 58 126 58 L214 58 Q222 58 226 62 L232 72 L232 88 Z" />
      <path className="ct" d="M170 59 L216 59 L224 66 L182 66 Z" />
      <path className="cf" d="M222 60 L230 62 L232 72 L224 72 Z" />
      <path className="cf" d="M236 74 L262 74 L258 90 L238 90 Z" />
      <path className="cf" d="M224 44 H231 V47 H224 Z" />
      <Wheel cx={70} r={22} rim={11} />
      <path className="cf" d="M20 28 H56 V34 H20 Z" />
      <path className="cb" d="M22 32 H54 V76 Q48 84 38 84 L22 72 Z" />
      <path className="ct" d="M24 40 H52 V46 H24 Z" />
      <path className="cf-line" d="M297 76 L299 86 M306 79 L308 86" />
      <path className="cf" d="M284 88 Q310 86 336 89 V92 H284 Z" />
      <path className="ct" d="M296 84 L332 82 L334 85 L298 87 Z" />
      <path className="cb" d="M326 76 H338 L340 93 H326 Z" />
      <Wheel cx={270} r={22} rim={11} />
    </>
  );
}

// ~2018-2021: long and low, thin-tipped nose, shark fin, big bargeboards,
// halo, dark rims with the compound stripe, and a DRS flap that opens.
function Drs() {
  return (
    <>
      <path className="cf" d="M44 88 H300 V91 H44 Z" />
      <Helmet cx={222} />
      <path className="cb" d="M168 35 L48 42 L48 48 L100 52 Z" />
      <path className="cb" d="M26 72 L40 62 L84 56 L170 34 L186 30 L190 38 L198 46 L238 47 L248 52 L284 58 L338 70 L354 75 Q358 78 352 80 L338 79 L292 73 L262 73 L256 88 L44 88 L30 80 Z" />
      <path className="ct" d="M100 56 L170 38 L176 40 L108 58 Z" />
      <path className="cf" d="M178 28 H190 V30 H178 Z M185 31 L190 31 L192 39 L187 39 Z" />
      <path className="cb" d="M120 88 L124 66 Q128 60 138 60 L232 60 Q242 60 246 66 L250 76 L250 88 Z" />
      <path className="ct" d="M150 70 H240 L236 74 H150 Z" />
      <path className="cf" d="M124 82 H250 V88 H122 Z M240 61 L248 64 L250 76 L242 76 Z" />
      <path className="cf" d="M254 72 H284 L282 90 H256 Z" />
      <path className="cf-line" d="M262 75 L261 88 M270 75 L269 88 M277 75 L276 88" />
      <path className="cf" d="M238 52 H246 V55 H238 Z" />
      <path className="halo" d="M196 43 Q220 36 244 42 L250 52" />
      <Wheel cx={60} r={22} rim={11} band />
      <path className="cf wing-flap" d="M12 34 L46 36 V41 L12 39 Z" />
      <path className="cb" d="M14 40 H46 V66 H30 Q20 66 14 60 Z" />
      <path className="ct" d="M16 48 H46 V54 H16 Z" />
      <path className="cf" d="M18 70 H46 V74 H18 Z" />
      <path className="cf-line" d="M331 77 L333 86 M344 79 L346 86" />
      <path className="cf" d="M318 88 Q350 86 384 88 V92 H318 Z" />
      <path className="cb" d="M326 84 Q354 80 380 80 V84 Q354 84 328 87 Z" />
      <path className="cb" d="M372 72 H388 L390 93 H372 Z" />
      <path className="ct" d="M372 89 H390 V93 H372 Z" />
      <Wheel cx={300} r={22} rim={11} band />
    </>
  );
}

// ~2022-2025: 18-inch wheels under covers, winglets over the front tyres, high
// sidepod inlets ramping down to the floor, a spoon rear wing, and front-wing
// elements sweeping up at the tips.
function GroundEffect() {
  return (
    <>
      <path className="cf" d="M50 90 H290 V93 H50 Z M90 86 Q180 82 270 86 V90 H90 Z" />
      <Helmet cx={224} />
      <path className="cb" d="M28 70 L44 60 L92 54 L172 34 L188 30 L192 38 L200 46 L240 47 L252 52 L300 60 L336 70 L352 80 L340 81 L300 75 L266 75 L260 90 L50 90 L32 80 Z" />
      <path className="cf" d="M92 54 L172 34 L180 36 L104 58 Z M184 31 L189 31 L192 38 L187 38 Z" />
      <path className="cb" d="M108 90 Q120 76 150 68 L230 58 Q244 56 250 62 L254 76 V90 Z" />
      <path className="cf" d="M112 90 Q130 82 160 80 H254 V90 Z M242 58 L250 60 L254 74 L246 74 Z" />
      <path className="cf" d="M240 50 H249 V53 H240 Z" />
      <path className="halo" d="M198 43 Q222 36 246 42 L252 52" />
      <Wheel cx={62} r={24} rim={16} band cover />
      <path className="cf wing-flap" d="M12 30 Q30 26 48 30 V35 Q30 32 12 36 Z" />
      <path className="cb" d="M14 38 Q14 34 20 34 H48 V66 Q30 66 18 58 Q14 52 14 44 Z" />
      <path className="cf" d="M20 70 H46 V73 H20 Z" />
      <path className="cf" d="M320 90 Q346 92 388 86 V90 Q346 95 320 93 Z" />
      <path className="cb" d="M326 86 Q352 86 384 78 L386 82 Q354 90 328 89 Z" />
      <path className="cf" d="M332 82 Q356 80 382 72 L384 76 Q358 84 334 85 Z" />
      <path className="cb" d="M378 70 H390 L392 92 H380 Z" />
      <Wheel cx={302} r={24} rim={16} band cover />
      <path className="cf" d="M290 46 Q302 42 316 46 L314 49 Q302 46 292 49 Z" />
      <path className="cf-line" d="M302 46 V50" />
    </>
  );
}

// 2026: shorter and narrower, no beam wing, and front and rear flaps that
// move together between Corner and Straight Mode.
function Hybrid() {
  return (
    <>
      <path className="cf" d="M56 90 H286 V93 H56 Z" />
      <Helmet cx={222} />
      <path className="cb" d="M36 70 L50 61 L96 55 L174 35 L188 31 L192 39 L200 46 L238 47 L250 52 L296 61 L330 70 L344 78 L332 80 L296 75 L264 75 L258 90 L56 90 L40 80 Z" />
      <path className="ct" d="M96 55 L174 35 L180 37 L106 59 Z" />
      <path className="cf" d="M184 32 L189 32 L192 39 L187 39 Z" />
      <path className="cb" d="M116 90 Q128 78 156 70 L228 60 Q240 58 246 63 L250 76 V90 Z" />
      <path className="cf" d="M120 90 Q136 83 164 81 H250 V90 Z M238 59 L246 61 L250 74 L242 74 Z" />
      <path className="cf" d="M236 50 H245 V53 H236 Z" />
      <path className="halo" d="M198 43 Q220 36 244 42 L250 52" />
      <Wheel cx={70} r={23} rim={15} band cover />
      <path className="ct wing-flap" d="M16 28 Q34 24 52 28 V33 Q34 30 16 34 Z" />
      <path className="cb" d="M18 38 Q18 34 24 34 H52 V64 Q36 64 24 58 Q18 52 18 44 Z" />
      <path className="cf" d="M314 89 Q340 91 378 86 V90 Q340 95 314 92 Z" />
      <path className="ct wing-flap" d="M320 85 Q344 85 374 78 L376 82 Q346 89 322 88 Z" />
      <path className="cb" d="M368 72 H380 L382 91 H370 Z" />
      <Wheel cx={296} r={23} rim={15} band cover />
    </>
  );
}

const CARS: Record<Era["id"], () => ReactNode> = {
  refuelling: Refuelling,
  drs: Drs,
  "ground-effect": GroundEffect,
  hybrid: Hybrid,
};

export default function RaceCar({ era }: { era: Era["id"] }) {
  const Car = CARS[era];
  return (
    <svg className="race-car" viewBox="0 0 400 100" aria-hidden="true">
      <Car />
    </svg>
  );
}
