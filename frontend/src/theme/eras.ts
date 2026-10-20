// One look per era of the rules. The colours, fonts and textures live in
// index.css under :root[data-era="..."]; this is the copy the hero shows and
// the key the CSS is selected by.
export interface Era {
  id: "refuelling" | "drs" | "ground-effect" | "hybrid";
  years: string;
  name: string;
  tagline: string;
}

// Newest first: a season belongs to the first era it reaches back to.
const ERAS: [number, Era][] = [
  [2026, {
    id: "hybrid",
    years: "2026–",
    name: "The Hybrid Era",
    tagline:
      "Power split almost evenly between combustion and electric. Active aero in Straight and Corner Mode, Overtake Mode within a second of the car ahead, and Boost anywhere on the lap.",
  }],
  [2022, {
    id: "ground-effect",
    years: "2022–2025",
    name: "The Ground-Effect Era",
    tagline:
      "Venturi floors and 18-inch wheels brought ground effect back, and porpoising with it, under a budget cap.",
  }],
  [2011, {
    id: "drs",
    years: "2011–2021",
    name: "The DRS Era",
    tagline:
      "A rear-wing flap that opened within a second of the car ahead. KERS, then V6 turbo hybrids from 2014, and the halo from 2018.",
  }],
  [0, {
    id: "refuelling",
    years: "2003–2010",
    name: "The Refuelling Era",
    tagline:
      "Grooved tyres, a Bridgestone–Michelin tyre war, the howl of V10s giving way to V8s in 2006, and refuelling stops until 2010.",
  }],
];

export function eraFor(season: number | null): Era {
  const year = season ?? new Date().getFullYear();
  return ERAS.find(([from]) => year >= from)![1];
}
