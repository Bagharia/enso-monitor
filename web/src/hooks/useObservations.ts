// Charge les observations à chaque changement de période, et expose l'état du chargement.
import { useEffect, useState } from "react";

import { fetchObservations } from "../api/observations";
import type { ObservationListResponse, Period } from "../types";

// Un seul état à la fois : impossible d'avoir "chargement" et "erreur" en même temps.
export type ObservationsState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: ObservationListResponse };

// Résultat d'une requête, étiqueté avec la période qu'il concerne.
type PeriodResult = { periodKey: string } & (
  | { status: "error"; message: string }
  | { status: "success"; data: ObservationListResponse }
);

export function useObservations({ startYear, endYear }: Period): ObservationsState {
  const periodKey = `${startYear}-${endYear}`;
  const [lastResult, setLastResult] = useState<PeriodResult | null>(null);

  useEffect(() => {
    // Si la période change avant la fin de la requête, on annule l'ancienne :
    // une réponse lente ne peut pas écraser une réponse plus récente.
    const controller = new AbortController();

    fetchObservations({ startYear, endYear }, controller.signal)
      .then((data) => setLastResult({ periodKey, status: "success", data }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message =
          error instanceof Error ? error.message : "Impossible de contacter l'API.";
        setLastResult({ periodKey, status: "error", message });
      });

    return () => controller.abort();
  }, [periodKey, startYear, endYear]);

  // Le chargement est déduit : tant que le dernier résultat ne concerne pas
  // la période demandée, c'est qu'on attend encore la réponse.
  if (lastResult === null || lastResult.periodKey !== periodKey) {
    return { status: "loading" };
  }
  return lastResult;
}
