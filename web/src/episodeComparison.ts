// Comparaison de deux épisodes : libellés et texte d'interprétation.
// Fonctions pures (aucun affichage, aucun appel réseau) : faciles à tester avec Vitest.
import { formatGap, formatValue } from "./format";
import type { EpisodeResponse, ObservationResponse } from "./types";

// En dessous de cet écart, deux pics sont jugés comparables (même ordre que les arrondis NOAA).
const COMPARABLE_PEAK_GAP = 0.1;

export interface ComparisonText {
  findings: string[]; // ce que montrent les mesures
  limits: string[]; // ce qu'elles ne permettent pas de conclure
}

// "1997-98" pour un épisode à cheval sur deux années, "2023" s'il tient dans une seule.
export function episodeLabel(episode: EpisodeResponse): string {
  const startYear = episode.start.year;
  const endYear = episode.end.year;
  return startYear === endYear ? `${startYear}` : `${startYear}-${String(endYear).slice(2)}`;
}

function seasonAndYear(observation: ObservationResponse): string {
  return `${observation.season} ${observation.year}`;
}

export function compareEpisodes(
  episodeA: EpisodeResponse,
  episodeB: EpisodeResponse,
  unit: string,
  episodeThreshold: number,
  minEpisodeSeasons: number,
): ComparisonText {
  const episodeALabel = episodeLabel(episodeA);
  const episodeBLabel = episodeLabel(episodeB);
  const findings: string[] = [];

  // 1. Intensité : comparaison des pics
  const peakGap = Math.abs(episodeA.peak.value - episodeB.peak.value);
  findings.push(
    `Pic : ${formatValue(episodeA.peak.value, unit)} en ${seasonAndYear(episodeA.peak)} ` +
      `pour ${episodeALabel}, ${formatValue(episodeB.peak.value, unit)} ` +
      `en ${seasonAndYear(episodeB.peak)} pour ${episodeBLabel}.`,
  );
  if (peakGap < COMPARABLE_PEAK_GAP) {
    findings.push("Les deux pics sont d'intensité comparable.");
  } else {
    const stronger = episodeA.peak.value > episodeB.peak.value ? episodeALabel : episodeBLabel;
    findings.push(`Le pic de ${stronger} est plus élevé de ${formatGap(peakGap, unit)}.`);
  }
  if (episodeA.peak.season === episodeB.peak.season) {
    findings.push(`Les deux pics sont atteints à la même saison (${episodeA.peak.season}).`);
  }

  // 2. Durée
  findings.push(
    `Durée : ${episodeA.duration_seasons} saisons pour ${episodeALabel} ` +
      `(${seasonAndYear(episodeA.start)} → ${seasonAndYear(episodeA.end)}), ` +
      `${episodeB.duration_seasons} saisons pour ${episodeBLabel} ` +
      `(${seasonAndYear(episodeB.start)} → ${seasonAndYear(episodeB.end)}).`,
  );
  const durationGap = episodeA.duration_seasons - episodeB.duration_seasons;
  if (durationGap === 0) {
    findings.push("Les deux épisodes ont la même durée selon cette règle.");
  } else {
    const longer = durationGap > 0 ? episodeALabel : episodeBLabel;
    const extraSeasons = Math.abs(durationGap);
    const seasonWord = extraSeasons === 1 ? "saison" : "saisons";
    findings.push(`${longer} a duré ${extraSeasons} ${seasonWord} de plus selon cette règle.`);
  }

  // 3. Limites : ce que la comparaison ne permet pas de dire
  const limits = [
    `Règle utilisée : un épisode El Niño compte au moins ${minEpisodeSeasons} saisons ` +
      `consécutives à ${formatValue(episodeThreshold, unit)} ou plus, sur les valeurs RONI à ` +
      "2 décimales. Avec des valeurs arrondies au dixième, une saison à +0,47 °C compterait " +
      "comme +0,5 °C : les durées peuvent changer.",
    "L'indice mesure l'intensité et la durée de l'anomalie de température, pas ses " +
      "conséquences (pluies, sécheresses, dégâts).",
    "Deux épisodes ne suffisent pas à dégager une tendance.",
  ];
  for (const episode of [episodeA, episodeB]) {
    if (episode.is_ongoing) {
      limits.push(
        `L'épisode ${episodeLabel(episode)} est en cours : sa durée et son pic peuvent évoluer.`,
      );
    }
  }

  return { findings, limits };
}
