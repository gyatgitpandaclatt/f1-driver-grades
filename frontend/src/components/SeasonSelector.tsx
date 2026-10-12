import { useLocation, useNavigate } from "react-router";

interface Props {
  seasons: number[];
  currentSeason: number | null;
  selectedSeason: number | null;
}

// The season every tab shows, kept in the URL (?season=2024; absent for the
// current season) so a season's page can be linked to and Back works.
export default function SeasonSelector({ seasons, currentSeason, selectedSeason }: Props) {
  const navigate = useNavigate();
  const location = useLocation();

  // Until the list arrives (or if it can't), show what's on screen, disabled.
  const options =
    selectedSeason != null && !seasons.includes(selectedSeason)
      ? [selectedSeason, ...seasons]
      : seasons;
  if (options.length === 0) return null;

  const choose = (season: number) => {
    const params = new URLSearchParams(location.search);
    const isPast = season !== currentSeason;
    if (isPast) {
      params.set("season", String(season));
    } else {
      params.delete("season");
    }
    // A finished season has a season summary in place of the race summary.
    let pathname = location.pathname;
    if (isPast && pathname === "/race-summary") pathname = "/season-summary";
    if (!isPast && pathname === "/season-summary") pathname = "/race-summary";
    const search = params.toString();
    navigate({ pathname, search: search ? `?${search}` : "" });
  };

  return (
    <label className="season-selector">
      <span className="season-selector-label">Season</span>
      <select
        value={selectedSeason ?? ""}
        disabled={seasons.length === 0 || currentSeason == null}
        onChange={(e) => choose(Number(e.target.value))}
      >
        {options.map((season) => (
          <option key={season} value={season}>
            {season === currentSeason ? `${season} · current` : season}
          </option>
        ))}
      </select>
    </label>
  );
}
