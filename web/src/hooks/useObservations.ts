// Charge les observations à chaque changement de période, et expose l'état du chargement.
import { useEffect, useState } from "react";

import { fetchObservations } from "../api/observations";
import type { ObservationListResponse, Period } from "../types";

// Un seul état à la fois : impossible d'avoir "chargement" et "erreur" en même temps.
export type ObservationsState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: ObservationListResponse };

// Résultat d'une requête, étiqueté avec la demande qu'il concerne (période + tentative).
type RequestResult = { requestKey: string } & (
  | { status: "error"; message: string }
  | { status: "success"; data: ObservationListResponse }
);

export interface ObservationsLoader {
  state: ObservationsState;
  retry: () => void; // relance la même demande (ex. après une erreur 503)
}

export function useObservations({ startYear, endYear }: Period): ObservationsLoader {
  // Chaque clic sur « Réessayer » crée une nouvelle tentative, donc une nouvelle demande.
  const [attempt, setAttempt] = useState(0);
  const requestKey = `${startYear}-${endYear}#${attempt}`;
  const [lastResult, setLastResult] = useState<RequestResult | null>(null);

  useEffect(() => {
    // Si la période change avant la fin de la requête, on annule l'ancienne :
    // une réponse lente ne peut pas écraser une réponse plus récente.
    const controller = new AbortController();

    fetchObservations({ startYear, endYear }, controller.signal)
      .then((data) => setLastResult({ requestKey, status: "success", data }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message =
          error instanceof Error ? error.message : "Impossible de contacter l'API.";
        setLastResult({ requestKey, status: "error", message });
      });

    return () => controller.abort();
  }, [requestKey, startYear, endYear]);

  const retry = () => setAttempt((previousAttempt) => previousAttempt + 1);

  // Le chargement est déduit : tant que le dernier résultat ne concerne pas
  // la demande en cours, c'est qu'on attend encore la réponse.
  if (lastResult === null || lastResult.requestKey !== requestKey) {
    return { state: { status: "loading" }, retry };
  }
  return { state: lastResult, retry };
}
