import { useOutletContext } from "react-router";
import type { DriverGrade, Meta } from "../api/types";

export interface LayoutContext {
  drivers: DriverGrade[];
  meta: Meta;
  season: number;
  // False for a finished season: its figures are final.
  isCurrentSeason: boolean;
  currentRound: number;
}

export function useLayoutData() {
  return useOutletContext<LayoutContext>();
}
