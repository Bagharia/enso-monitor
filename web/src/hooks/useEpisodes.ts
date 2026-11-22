// Charge la liste des épisodes d'une phase, et expose l'état du chargement.
import { useEffect, useState } from "react";

import { fetchEpisodes } from "../api/episodes";
import type { EpisodeListResponse, Phase } from "../types";

// Un seul état à la fois, comme pour useObservations.
export type EpisodesState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: EpisodeListResponse };

// Résultat d'une requête, étiqueté avec la demande qu'il concerne (phase + tentative).
type RequestResult = { requestKey: string } & (
  | { status: "error"; message: string }
  | { status: "success"; data: EpisodeListResponse }
);

export interface EpisodesLoader {
  state: EpisodesState;
  retry: () => void; // relance la même demande (ex. après une erreur 503)
}

export function useEpisodes(phase: Phase): EpisodesLoader {
  // Même principe que useObservations : chaque « Réessayer » est une nouvelle tentative.
  const [attempt, setAttempt] = useState(0);
  const requestKey = `${phase}#${attempt}`;
  const [lastResult, setLastResult] = useState<RequestResult | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    fetchEpisodes(phase, controller.signal)
      .then((data) => setLastResult({ requestKey, status: "success", data }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message =
          error instanceof Error ? error.message : "Impossible de contacter l'API.";
        setLastResult({ requestKey, status: "error", message });
      });

    return () => controller.abort();
  }, [requestKey, phase]);

  const retry = () => setAttempt((previousAttempt) => previousAttempt + 1);

  if (lastResult === null || lastResult.requestKey !== requestKey) {
    return { state: { status: "loading" }, retry };
  }
  return { state: lastResult, retry };
}
