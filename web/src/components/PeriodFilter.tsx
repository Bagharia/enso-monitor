// Choix de la période affichée (années de début et de fin, incluses).
import { useId } from "react";

import type { Period } from "../types";

interface PeriodFilterProps {
  period: Period;
  minYear: number;
  maxYear: number;
  onChange: (period: Period) => void;
}

export function PeriodFilter({ period, minYear, maxYear, onChange }: PeriodFilterProps) {
  const startId = useId();
  const endId = useId();
  const years = Array.from({ length: maxYear - minYear + 1 }, (_, offset) => minYear + offset);

  // Les listes ne proposent que des années cohérentes : la fin ne peut pas précéder le début.
  return (
    <fieldset className="period-filter">
      <legend>Période</legend>

      <label htmlFor={startId}>De</label>
      <select
        id={startId}
        value={period.startYear}
        onChange={(event) => onChange({ ...period, startYear: Number(event.target.value) })}
      >
        {years
          .filter((year) => year <= period.endYear)
          .map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
      </select>

      <label htmlFor={endId}>à</label>
      <select
        id={endId}
        value={period.endYear}
        onChange={(event) => onChange({ ...period, endYear: Number(event.target.value) })}
      >
        {years
          .filter((year) => year >= period.startYear)
          .map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
      </select>
    </fieldset>
  );
}
