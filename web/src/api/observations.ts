// Appel à GET /api/v1/observations : les valeurs de l'indice sur une période.
import type { ObservationListResponse, Period } from "../types";
import { getJson } from "./client";

export function fetchObservations(
  period: Period,
  signal?: AbortSignal,
): Promise<ObservationListResponse> {
  return getJson<ObservationListResponse>(
    "/observations",
    { start: `${period.startYear}-01-01`, end: `${period.endYear}-12-31` },
    signal,
  );
}
