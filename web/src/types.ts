// Types des réponses de l'API : copie exacte des schémas Pydantic (backend/app/schemas.py).

export interface SourceResponse {
  provider: string;
  url: string;
  extracted_on: string; // date ISO "AAAA-MM-JJ"
}

export interface ObservationResponse {
  season: string; // "DJF", "JFM", ...
  year: number;
  period_date: string; // 1er jour du mois central, "AAAA-MM-JJ"
  value: number; // anomalie en °C
}

export interface ObservationListResponse {
  index_code: string;
  index_name: string;
  unit: string;
  source: SourceResponse;
  start: string | null;
  end: string | null;
  count: number;
  observations: ObservationResponse[];
}

export type Phase = "el_nino" | "la_nina";

export interface EpisodeResponse {
  phase: Phase;
  start: ObservationResponse; // première saison de l'épisode
  end: ObservationResponse; // dernière saison de l'épisode
  peak: ObservationResponse; // saison la plus intense
  duration_seasons: number;
  is_ongoing: boolean;
  observations: ObservationResponse[];
}

export interface EpisodeListResponse {
  index_code: string;
  unit: string;
  source: SourceResponse;
  phase: Phase;
  episode_threshold: number; // seuil en valeur absolue (°C)
  min_episode_seasons: number;
  episodes: EpisodeResponse[];
}

// Période choisie par l'utilisateur, en années entières (bornes incluses).
export interface Period {
  startYear: number;
  endYear: number;
}
