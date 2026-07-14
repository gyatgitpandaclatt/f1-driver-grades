import { useOutletContext } from "react-router-dom";
import type { DriverGrade, Meta } from "../api/types";

export interface LayoutContext {
  drivers: DriverGrade[];
  meta: Meta;
  season: number;
  currentRound: number;
}

export function useLayoutData() {
  return useOutletContext<LayoutContext>();
}
