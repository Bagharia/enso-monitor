// Charge une fois la liste des épisodes d'une phase, et expose l'état du chargement.
import { useEffect, useState } from "react";

import { fetchEpisodes } from "../api/episodes";
import type { EpisodeListResponse, Phase } from "../types";

// Un seul état à la fois, comme pour useObservations.
export type EpisodesState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: EpisodeListResponse };

export function useEpisodes(phase: Phase): EpisodesState {
  const [state, setState] = useState<EpisodesState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    fetchEpisodes(phase, controller.signal)
      .then((data) => setState({ status: "success", data }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message =
          error instanceof Error ? error.message : "Impossible de contacter l'API.";
        setState({ status: "error", message });
      });

    return () => controller.abort();
  }, [phase]);

  return state;
}
