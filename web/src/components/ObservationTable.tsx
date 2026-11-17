// Tableau des valeurs : alternative accessible à la courbe (lecteurs d'écran, clavier).
import { formatValue } from "../format";
import type { ObservationResponse } from "../types";

interface ObservationTableProps {
  observations: ObservationResponse[];
  unit: string;
}

export function ObservationTable({ observations, unit }: ObservationTableProps) {
  return (
    <details className="observation-table">
      <summary>Voir les {observations.length} valeurs sous forme de tableau</summary>
      <table>
        <caption>Valeurs de l'indice par saison de 3 mois ({unit})</caption>
        <thead>
          <tr>
            <th scope="col">Saison</th>
            <th scope="col">Année</th>
            <th scope="col">Anomalie</th>
          </tr>
        </thead>
        <tbody>
          {observations.map((observation) => (
            <tr key={`${observation.year}-${observation.season}`}>
              <td>{observation.season}</td>
              <td>{observation.year}</td>
              <td>{formatValue(observation.value, unit)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
