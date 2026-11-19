// Axe vertical des courbes : borne arrondie et graduations régulières.
// Partagé par ObservationChart et EpisodeComparison pour que les deux courbes suivent la même
// règle : une graduation tous les 0,5 °C, donc le 0 et les seuils ±0,5 °C ont toujours la leur.

export const AXIS_STEP = 0.5; // °C entre deux graduations

// Arrondit au pas supérieur : 2,28 → 2,5 ; 2,5 → 2,5.
export function roundUpToAxisStep(value: number): number {
  return Math.ceil(value / AXIS_STEP) * AXIS_STEP;
}

// Graduations de axisMin à axisMax inclus, tous les AXIS_STEP (bornes multiples du pas).
export function axisTicks(axisMin: number, axisMax: number): number[] {
  const tickCount = Math.round((axisMax - axisMin) / AXIS_STEP) + 1;
  return Array.from({ length: tickCount }, (_, position) => axisMin + position * AXIS_STEP);
}
