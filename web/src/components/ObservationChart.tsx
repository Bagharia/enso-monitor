// Courbe de l'indice dans le temps, avec les seuils El Niño / La Niña.
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

import { formatAxisValue, formatValue } from "../format";
import type { ObservationResponse } from "../types";

// Seuils NOAA : ±0,5 °C (sur 5 saisons consécutives pour parler d'épisode).
const EL_NINO_THRESHOLD = 0.5;
const LA_NINA_THRESHOLD = -0.5;
const ANOMALY_COLOR = "#222222";
const EL_NINO_COLOR = "#b4232a";
const LA_NINA_COLOR = "#1f5fa8";
const AXIS_STEP = 0.5; // une graduation tous les 0,5 °C

interface ObservationChartProps {
  observations: ObservationResponse[];
  indexCode: string;
  unit: string;
}

export function ObservationChart({ observations, indexCode, unit }: ObservationChartProps) {
  const highest = observations.reduce((highestSoFar, observation) =>
    observation.value > highestSoFar.value ? observation : highestSoFar,
  );
  const lowest = observations.reduce((lowestSoFar, observation) =>
    observation.value < lowestSoFar.value ? observation : lowestSoFar,
  );
  const first = observations[0];
  const last = observations[observations.length - 1];

  // Axe vertical symétrique autour de 0, arrondi au demi-degré supérieur :
  // El Niño (au-dessus) et La Niña (en dessous) sont dessinés à la même échelle.
  const largestDeviation = Math.max(Math.abs(highest.value), Math.abs(lowest.value), 1);
  const axisLimit = Math.ceil(largestDeviation / AXIS_STEP) * AXIS_STEP;
  // Graduations régulières tous les 0,5 °C : le 0 et les deux seuils ont toujours la leur.
  const axisTicks = Array.from(
    { length: Math.round((2 * axisLimit) / AXIS_STEP) + 1 },
    (_, position) => -axisLimit + position * AXIS_STEP,
  );

  // Résumé textuel affiché sous la courbe : c'est aussi ce que lit un lecteur d'écran.
  const summary =
    `Courbe ${indexCode} de ${first.season} ${first.year} à ${last.season} ${last.year}, ` +
    `${observations.length} valeurs. Maximum ${formatValue(highest.value, unit)} ` +
    `(${highest.season} ${highest.year}), minimum ${formatValue(lowest.value, unit)} ` +
    `(${lowest.season} ${lowest.year}).`;

  return (
    <figure className="chart">
      {/* Le dessin est masqué aux lecteurs d'écran : ils lisent le résumé et le tableau. */}
      <div aria-hidden="true">
        <ResponsiveContainer width="100%" height={360}>
          <LineChart
            data={observations}
            margin={{ top: 16, right: 24, bottom: 8, left: 8 }}
            accessibilityLayer={false}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period_date" tickFormatter={(date: string) => date.slice(0, 4)} />
            <YAxis
              domain={[-axisLimit, axisLimit]}
              ticks={axisTicks}
              tickFormatter={(value: number) => formatAxisValue(value, unit)}
              width={72}
            />
            <Tooltip
              labelFormatter={(_, payload) => {
                const observation = payload?.[0]?.payload as ObservationResponse | undefined;
                return observation ? `${observation.season} ${observation.year}` : "";
              }}
              formatter={(value) => [formatValue(Number(value), unit), indexCode]}
            />
            <ReferenceLine y={EL_NINO_THRESHOLD} stroke={EL_NINO_COLOR} strokeDasharray="6 4" />
            <ReferenceLine y={LA_NINA_THRESHOLD} stroke={LA_NINA_COLOR} strokeDasharray="6 4" />
            <Line
              type="monotone"
              dataKey="value"
              stroke={ANOMALY_COLOR}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Légende en HTML sous la courbe : lisible quelle que soit la largeur de l'écran. */}
      <ul className="chart-legend">
        <li>
          <span
            className="legend-line"
            style={{ borderTopColor: ANOMALY_COLOR, borderTopStyle: "solid" }}
          />
          Anomalie {indexCode} ({unit})
        </li>
        <li>
          <span className="legend-line" style={{ borderTopColor: EL_NINO_COLOR }} />
          Seuil El Niño ({formatValue(EL_NINO_THRESHOLD, unit)})
        </li>
        <li>
          <span className="legend-line" style={{ borderTopColor: LA_NINA_COLOR }} />
          Seuil La Niña ({formatValue(LA_NINA_THRESHOLD, unit)})
        </li>
      </ul>
      <figcaption>{summary}</figcaption>
    </figure>
  );
}
