import { useEffect, useState } from "react";
import { fetchSeasons } from "../api/client";

interface Seasons {
  // null until loaded, and if the list could not be fetched — the grades
  // still load for the current season, the selector just has nothing to offer.
  current: number | null;
  seasons: number[];
}

export function useSeasons(): Seasons {
  const [state, setState] = useState<Seasons>({ current: null, seasons: [] });

  useEffect(() => {
    let active = true;
    fetchSeasons()
      .then((result) => {
        if (active && "seasons" in result) {
          setState({ current: result.current, seasons: result.seasons });
        }
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  return state;
}
