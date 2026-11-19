// Test du calcul de l'axe vertical (src/chartAxis.ts).
import { expect, test } from "vitest";

import { axisTicks, roundUpToAxisStep } from "./chartAxis";

test("rounds the axis limit up to the next step", () => {
  expect(roundUpToAxisStep(2.28)).toBe(2.5);
  expect(roundUpToAxisStep(2.5)).toBe(2.5);
});

test("ticks every step, including zero and both thresholds", () => {
  expect(axisTicks(-1, 1)).toEqual([-1, -0.5, 0, 0.5, 1]);
  expect(axisTicks(0, 2.5)).toEqual([0, 0.5, 1, 1.5, 2, 2.5]);
});
