// Mise en forme des nombres et des dates pour un affichage en français.

const valueFormatter = new Intl.NumberFormat("fr-FR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  signDisplay: "exceptZero", // "+2,28" pour rendre visible le signe de l'anomalie
});

const axisValueFormatter = new Intl.NumberFormat("fr-FR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  signDisplay: "exceptZero", // graduations : "+0,5", "0,0", "−0,5"
});

const gapFormatter = new Intl.NumberFormat("fr-FR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
}); // écart entre deux valeurs : toujours positif, sans signe

export function formatGap(gap: number, unit: string): string {
  return `${gapFormatter.format(Math.abs(gap))} ${unit}`;
}

export function formatValue(value: number, unit: string): string {
  return `${valueFormatter.format(value)} ${unit}`;
}

export function formatAxisValue(value: number, unit: string): string {
  return `${axisValueFormatter.format(value)} ${unit}`;
}

export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}
