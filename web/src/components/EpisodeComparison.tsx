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

// Épisodes comparés par défaut : les deux El Niño les plus forts de la série (choix du projet).
const DEFAULT_START_YEARS = [1997, 2015] as const;
const FIRST_COLOR = "#b4232a";
const SECOND_COLOR = "#1f5fa8";

interface EpisodeComparisonProps {
  episodeList: EpisodeListResponse;
}

function defaultEpisodeIndex(episodes: EpisodeResponse[], startYear: number, fallback: number) {
  const position = episodes.findIndex((episode) => episode.start.year === startYear);
  return position === -1 ? fallback : position;
}

export function EpisodeComparison({ episodeList }: EpisodeComparisonProps) {
  const { episodes, unit, threshold, min_duration_seasons } = episodeList;
  const firstSelectId = useId();
  const secondSelectId = useId();
  const [firstIndex, setFirstIndex] = useState(() =>
    defaultEpisodeIndex(episodes, DEFAULT_START_YEARS[0], 0),
  );
  const [secondIndex, setSecondIndex] = useState(() =>
    defaultEpisodeIndex(episodes, DEFAULT_START_YEARS[1], episodes.length - 1),
  );

  if (episodes.length < 2) {
    return <p>Pas assez d'épisodes détectés pour faire une comparaison.</p>;
  }

  const first = episodes[firstIndex];
  const second = episodes[secondIndex];
  const comparedEpisodes = [
    { letter: "A", episode: first },
    { letter: "B", episode: second },
  ];
  const firstLabel = episodeLabel(first);
  const secondLabel = episodeLabel(second);
  const { findings, limits } = compareEpisodes(
    first,
    second,
    unit,
    threshold,
    min_duration_seasons,
  );

  // Courbes alignées sur la 1re saison de chaque épisode : on compare leur forme, pas leur date.
  const longestDuration = Math.max(first.duration_seasons, second.duration_seasons);
  const alignedRows = Array.from({ length: longestDuration }, (_, position) => ({
    seasonNumber: position + 1,
    first: first.observations[position]?.value,
    second: second.observations[position]?.value,
  }));

  const episodeOptions = episodes.map((episode, position) => (
    <option key={episode.start.period_date} value={position}>
      {episodeLabel(episode)} ({episode.duration_seasons} saisons)
    </option>
  ));

  return (
    <section className="episode-comparison" aria-labelledby="comparison-title">
      <h2 id="comparison-title">Comparer deux épisodes El Niño</h2>

      <fieldset className="period-filter">
        <legend>Épisodes comparés</legend>
        <label htmlFor={firstSelectId}>Épisode A</label>
        <select
          id={firstSelectId}
          value={firstIndex}
          onChange={(event) => setFirstIndex(Number(event.target.value))}
        >
          {episodeOptions}
        </select>
        <label htmlFor={secondSelectId}>Épisode B</label>
        <select
          id={secondSelectId}
          value={secondIndex}
          onChange={(event) => setSecondIndex(Number(event.target.value))}
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
                domain={[0, "auto"]}
                tickFormatter={(value: number) => formatAxisValue(value, unit)}
                width={72}
              />
              <Tooltip
                labelFormatter={(seasonNumber) => `Saison n° ${seasonNumber}`}
                formatter={(value, name) => [
                  formatValue(Number(value), unit),
                  name === "first" ? firstLabel : secondLabel,
                ]}
              />
              <ReferenceLine y={threshold} stroke="#666666" strokeDasharray="6 4" />
              <Line
                dataKey="first"
                stroke={FIRST_COLOR}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                dataKey="second"
                stroke={SECOND_COLOR}
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
              style={{ borderTopColor: FIRST_COLOR, borderTopStyle: "solid" }}
            />
            A : {firstLabel}
          </li>
          <li>
            <span
              className="legend-line"
              style={{ borderTopColor: SECOND_COLOR, borderTopStyle: "solid" }}
            />
            B : {secondLabel}
          </li>
          <li>
            <span className="legend-line" style={{ borderTopColor: "#666666" }} />
            Seuil El Niño ({formatValue(threshold, unit)})
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
