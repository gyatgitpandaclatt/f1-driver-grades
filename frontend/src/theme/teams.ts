// Each constructor's main livery colour, for the stripe down a driver's row,
// the way the TV timing tower shows it. Names are Jolpica's, 2003 on; some
// teams changed colour over the years, so a few depend on the season.
type Livery = string | ((season: number) => string);

const LIVERIES: Record<string, Livery> = {
  Ferrari: "#dc0000",
  McLaren: (s) => (s >= 2017 ? "#ff8000" : "#b8bec6"),
  Mercedes: "#27f4d2",
  "Red Bull": "#2b4a9e",
  Renault: (s) => (s <= 2010 ? "#1e5bc6" : s === 2011 ? "#c8a24a" : "#ffd200"),
  Williams: (s) => (s >= 2014 && s <= 2018 ? "#f2f4f7" : "#1f5dbf"),
  Jaguar: "#0f6b3a",
  Jordan: "#f2c500",
  BAR: "#f2f2f2",
  Minardi: "#4a4a4a",
  Sauber: (s) => (s >= 2024 ? "#52e252" : s <= 2005 ? "#2c4b9b" : "#9aa3ad"),
  "BMW Sauber": "#c9d6ea",
  Toyota: "#e6e9ed",
  Honda: "#e6e9ed",
  MF1: "#c8c8c8",
  "Spyker MF1": "#ff7a00",
  Spyker: "#ff7a00",
  "Super Aguri": "#e0e0e0",
  "Toro Rosso": "#2f3f8f",
  AlphaTauri: "#2b4562",
  "RB F1 Team": "#6692ff",
  "Force India": (s) => (s >= 2017 ? "#f596c8" : "#ff8c00"),
  "Racing Point": "#f596c8",
  "Aston Martin": "#006f62",
  Brawn: "#dfff4f",
  Virgin: "#c00000",
  HRT: "#8a8a8a",
  "Lotus Racing": "#00573f",
  "Team Lotus": "#00573f",
  "Lotus F1": "#c8a24a",
  Caterham: "#005030",
  Marussia: "#a8102a",
  "Manor Marussia": "#a8102a",
  "Haas F1 Team": "#b6babd",
  "Alfa Romeo": "#9b0000",
  "Alpine F1 Team": "#0093cc",
  Audi: "#f50537",
  "Cadillac F1 Team": "#d0d4d8",
};

// shortcut: a constructor missing above gets a neutral grey; add it when a
// new team joins the grid.
export function teamColor(constructor: string, season: number): string {
  const livery = LIVERIES[constructor];
  if (livery == null) return "#6b6b7a";
  return typeof livery === "function" ? livery(season) : livery;
}
