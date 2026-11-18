// Section « Comparer deux épisodes » : choix, tableau, courbes superposées et interprétation.
import { useId, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { compareEpisodes, episodeLabel } from "../episodeComparison";
import { formatAxisValue, formatValue } from "../format";
import type { EpisodeListResponse, EpisodeResponse } from "../types";

// Épisodes comparés par défaut : choix du projet, deux El Niño forts à 18 ans d'écart.
const DEFAULT_START_YEARS = [1997, 2015] as const;
const EPISODE_A_COLOR = "#b4232a";
const EPISODE_B_COLOR = "#1f5fa8";
const THRESHOLD_COLOR = "#666666";
const AXIS_STEP = 0.5; // une graduation tous les 0,5 °C, comme la courbe principale

interface EpisodeComparisonProps {
  episodeList: EpisodeListResponse;
}

function defaultEpisodeIndex(episodes: EpisodeResponse[], startYear: number, fallback: number) {
  const position = episodes.findIndex((episode) => episode.start.year === startYear);
  return position === -1 ? fallback : position;
}

export function EpisodeComparison({ episodeList }: EpisodeComparisonProps) {
  const { episodes, unit, episode_threshold, min_episode_seasons } = episodeList;
  const titleId = useId();
  const episodeASelectId = useId();
  const episodeBSelectId = useId();
  const [episodeAIndex, setEpisodeAIndex] = useState(() =>
    defaultEpisodeIndex(episodes, DEFAULT_START_YEARS[0], 0),
  );
  const [episodeBIndex, setEpisodeBIndex] = useState(() =>
    defaultEpisodeIndex(episodes, DEFAULT_START_YEARS[1], episodes.length - 1),
  );

  if (episodes.length < 2) {
    return <p>Pas assez d'épisodes détectés pour faire une comparaison.</p>;
  }

  const episodeA = episodes[episodeAIndex];
  const episodeB = episodes[episodeBIndex];
  const comparedEpisodes = [
    { letter: "A", episode: episodeA },
    { letter: "B", episode: episodeB },
  ];
  const episodeALabel = episodeLabel(episodeA);
  const episodeBLabel = episodeLabel(episodeB);
  const { findings, limits } = compareEpisodes(
    episodeA,
    episodeB,
    unit,
    episode_threshold,
    min_episode_seasons,
  );

  // Courbes alignées sur la 1re saison de chaque épisode : on compare leur forme, pas leur date.
  const longestDuration = Math.max(episodeA.duration_seasons, episodeB.duration_seasons);
  const alignedRows = Array.from({ length: longestDuration }, (_, position) => ({
    seasonNumber: position + 1,
    episodeA: episodeA.observations[position]?.value,
    episodeB: episodeB.observations[position]?.value,
  }));

  // Axe vertical de 0 au plus haut pic arrondi au demi-degré supérieur, graduation tous les
  // 0,5 °C : le seuil +0,5 °C a toujours la sienne (même logique qu'ObservationChart).
  const highestPeak = Math.max(episodeA.peak.value, episodeB.peak.value, AXIS_STEP);
  const axisLimit = Math.ceil(highestPeak / AXIS_STEP) * AXIS_STEP;
  const axisTicks = Array.from(
    { length: Math.round(axisLimit / AXIS_STEP) + 1 },
    (_, position) => position * AXIS_STEP,
  );

  const episodeOptions = episodes.map((episode, position) => (
    <option key={episode.start.period_date} value={position}>
      {episodeLabel(episode)} ({episode.duration_seasons} saisons)
    </option>
  ));

  return (
    <section className="episode-comparison" aria-labelledby={titleId}>
      <h2 id={titleId}>Comparer deux épisodes El Niño</h2>

      <fieldset className="period-filter">
        <legend>Épisodes comparés</legend>
        <label htmlFor={episodeASelectId}>Épisode A</label>
        <select
          id={episodeASelectId}
          value={episodeAIndex}
          onChange={(event) => setEpisodeAIndex(Number(event.target.value))}
        >
          {episodeOptions}
        </select>
        <label htmlFor={episodeBSelectId}>Épisode B</label>
        <select
          id={episodeBSelectId}
          value={episodeBIndex}
          onChange={(event) => setEpisodeBIndex(Number(event.target.value))}
        >
          {episodeOptions}
        </select>
      </fieldset>

      <div className="table-scroll">
        <table>
          <caption>Mesures des deux épisodes (indice {episodeList.index_code})</caption>
          <thead>
            <tr>
              <th scope="col">Épisode</th>
              <th scope="col">Début</th>
              <th scope="col">Fin</th>
              <th scope="col">Durée</th>
              <th scope="col">Pic</th>
            </tr>
          </thead>
          <tbody>
            {comparedEpisodes.map(({ letter, episode }) => (
              <tr key={letter}>
                <th scope="row">
                  {letter} : {episodeLabel(episode)}
                </th>
                <td>{`${episode.start.season} ${episode.start.year}`}</td>
                <td>
                  {`${episode.end.season} ${episode.end.year}`}
                  {episode.is_ongoing && " (en cours)"}
                </td>
                <td>{episode.duration_seasons} saisons</td>
                <td>
                  {`${formatValue(episode.peak.value, unit)} `}
                  {`(${episode.peak.season} ${episode.peak.year})`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <figure className="chart">
        {/* Dessin masqué aux lecteurs d'écran : le tableau ci-dessus et le texte suffisent. */}
        <div aria-hidden="true">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={alignedRows}
              margin={{ top: 16, right: 24, bottom: 8, left: 8 }}
              accessibilityLayer={false}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="seasonNumber" />
              <YAxis
                domain={[0, axisLimit]}
                ticks={axisTicks}
                tickFormatter={(value: number) => formatAxisValue(value, unit)}
                width={72}
              />
              <Tooltip
                labelFormatter={(seasonNumber) => `Saison n° ${seasonNumber}`}
                formatter={(value, name) => [
                  formatValue(Number(value), unit),
                  name === "episodeA" ? episodeALabel : episodeBLabel,
                ]}
              />
              <ReferenceLine y={episode_threshold} stroke={THRESHOLD_COLOR} strokeDasharray="6 4" />
              <Line
                dataKey="episodeA"
                stroke={EPISODE_A_COLOR}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                dataKey="episodeB"
                stroke={EPISODE_B_COLOR}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <ul className="chart-legend">
          <li>
            <span
              className="legend-line"
              style={{ borderTopColor: EPISODE_A_COLOR, borderTopStyle: "solid" }}
            />
            A : {episodeALabel}
          </li>
          <li>
            <span
              className="legend-line"
              style={{ borderTopColor: EPISODE_B_COLOR, borderTopStyle: "solid" }}
            />
            B : {episodeBLabel}
          </li>
          <li>
            <span className="legend-line" style={{ borderTopColor: THRESHOLD_COLOR }} />
            Seuil El Niño ({formatValue(episode_threshold, unit)})
          </li>
        </ul>
        <figcaption>
          Axe horizontal : numéro de la saison depuis le début de chaque épisode.
        </figcaption>
      </figure>

      <h3>Ce que montrent les mesures</h3>
      <ul>
        {findings.map((finding) => (
          <li key={finding}>{finding}</li>
        ))}
      </ul>

      <h3>Limites de cette comparaison</h3>
      <ul>
        {limits.map((limit) => (
          <li key={limit}>{limit}</li>
        ))}
      </ul>
    </section>
  );
}
