// Test de l'interprétation de la comparaison (src/episodeComparison.ts).
import { expect, test } from "vitest";

import { compareEpisodes, episodeLabel } from "./episodeComparison";
import type { EpisodeResponse, ObservationResponse } from "./types";

function season(name: string, year: number, month: number, value: number): ObservationResponse {
  return { season: name, year, period_date: `${year}-${String(month).padStart(2, "0")}-01`, value };
}

// Bornes et pics réels des deux épisodes (API sur le fichier NOAA RONI du 14/11/2026).
const EPISODE_1997: EpisodeResponse = {
  phase: "el_nino",
  start: season("AMJ", 1997, 5, 0.83),
  end: season("MAM", 1998, 4, 0.81),
  peak: season("NDJ", 1997, 12, 2.28),
  duration_seasons: 12,
  is_ongoing: false,
  observations: [],
};
const EPISODE_2015: EpisodeResponse = {
  phase: "el_nino",
  start: season("FMA", 2015, 3, 0.59),
  end: season("MAM", 2016, 4, 0.65),
  peak: season("NDJ", 2015, 12, 2.25),
  duration_seasons: 14,
  is_ongoing: false,
  observations: [],
};

test("labels an episode spanning two years", () => {
  expect(episodeLabel(EPISODE_1997)).toBe("1997-98");
});

test("states comparable peaks, longer duration and the limits", () => {
  const { findings, limits } = compareEpisodes(EPISODE_1997, EPISODE_2015, "°C", 0.5, 5);

  expect(findings).toContain("Les deux pics sont d'intensité comparable.");
  expect(findings).toContain("Les deux pics sont atteints à la même saison (NDJ).");
  expect(findings).toContain("2015-16 a duré 2 saisons de plus selon cette règle.");
  expect(limits.some((limit) => limit.includes("pas ses conséquences"))).toBe(true);
  expect(limits.some((limit) => limit.includes("en cours"))).toBe(false);
});

test("mentions an ongoing episode", () => {
  const ongoing = { ...EPISODE_2015, is_ongoing: true };

  const { limits } = compareEpisodes(EPISODE_1997, ongoing, "°C", 0.5, 5);

  expect(limits).toContain(
    "L'épisode 2015-16 est en cours : sa durée et son pic peuvent évoluer.",
  );
});
