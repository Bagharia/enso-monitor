// Comparaison de deux épisodes : libellés et texte d'interprétation.
// Fonctions pures (aucun affichage, aucun appel réseau) : faciles à tester avec Vitest.
import { formatGap, formatValue } from "./format";
import type { EpisodeResponse } from "./types";

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

function seasonName(episodeSeason: EpisodeResponse["start"]): string {
  return `${episodeSeason.season} ${episodeSeason.year}`;
}

export function compareEpisodes(
  first: EpisodeResponse,
  second: EpisodeResponse,
  unit: string,
  threshold: number,
  minDurationSeasons: number,
): ComparisonText {
  const firstLabel = episodeLabel(first);
  const secondLabel = episodeLabel(second);
  const findings: string[] = [];

  // 1. Intensité : comparaison des pics
  const peakGap = Math.abs(first.peak.value - second.peak.value);
  findings.push(
    `Pic : ${formatValue(first.peak.value, unit)} en ${seasonName(first.peak)} pour ` +
      `${firstLabel}, ${formatValue(second.peak.value, unit)} en ${seasonName(second.peak)} ` +
      `pour ${secondLabel}.`,
  );
  if (peakGap < COMPARABLE_PEAK_GAP) {
    findings.push("Les deux pics sont d'intensité comparable.");
  } else {
    const stronger = first.peak.value > second.peak.value ? firstLabel : secondLabel;
    findings.push(`Le pic de ${stronger} est plus élevé de ${formatGap(peakGap, unit)}.`);
  }
  if (first.peak.season === second.peak.season) {
    findings.push(`Les deux pics sont atteints à la même saison (${first.peak.season}).`);
  }

  // 2. Durée
  findings.push(
    `Durée : ${first.duration_seasons} saisons pour ${firstLabel} ` +
      `(${seasonName(first.start)} → ${seasonName(first.end)}), ` +
      `${second.duration_seasons} saisons pour ${secondLabel} ` +
      `(${seasonName(second.start)} → ${seasonName(second.end)}).`,
  );
  const durationGap = first.duration_seasons - second.duration_seasons;
  if (durationGap === 0) {
    findings.push("Les deux épisodes ont la même durée selon cette règle.");
  } else {
    const longer = durationGap > 0 ? firstLabel : secondLabel;
    const extraSeasons = Math.abs(durationGap);
    const seasonWord = extraSeasons === 1 ? "saison" : "saisons";
    findings.push(`${longer} a duré ${extraSeasons} ${seasonWord} de plus selon cette règle.`);
  }

  // 3. Limites : ce que la comparaison ne permet pas de dire
  const limits = [
    `Règle utilisée : un épisode El Niño compte au moins ${minDurationSeasons} saisons ` +
      `consécutives à ${formatValue(threshold, unit)} ou plus, sur les valeurs RONI à ` +
      "2 décimales. Avec des valeurs arrondies au dixième (comme dans le tableau publié par " +
      "la NOAA), une saison à +0,47 °C compterait comme +0,5 °C : les durées peuvent changer.",
    "L'indice mesure l'intensité et la durée de l'anomalie de température, pas ses " +
      "conséquences (pluies, sécheresses, dégâts).",
    "Deux épisodes ne suffisent pas à dégager une tendance.",
  ];
  for (const episode of [first, second]) {
    if (episode.is_ongoing) {
      limits.push(
        `L'épisode ${episodeLabel(episode)} est en cours : sa durée et son pic peuvent évoluer.`,
      );
    }
  }

  return { findings, limits };
}
