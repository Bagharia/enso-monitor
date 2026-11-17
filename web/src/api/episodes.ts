// Appel à GET /api/v1/episodes : les épisodes El Niño ou La Niña détectés par l'API.
import type { EpisodeListResponse, Phase } from "../types";
import { getJson } from "./client";

export function fetchEpisodes(phase: Phase, signal?: AbortSignal): Promise<EpisodeListResponse> {
  return getJson<EpisodeListResponse>("/episodes", { phase }, signal);
}
