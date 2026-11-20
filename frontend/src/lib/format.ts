export const fmt = (value: number | null | undefined, digits = 4) =>
  value == null || !Number.isFinite(value) ? "—" : value.toFixed(digits);

export const pct = (value: number, digits = 2) => `${(value * 100).toFixed(digits)}%`;

export const MODEL_LABELS: Record<string, string> = {
  black_scholes: "Black-Scholes",
  binomial: "Binomial (CRR)",
  monte_carlo: "Monte Carlo",
  asian: "Asian (MC)",
  barrier: "Barrier (MC)",
};

export const modelLabel = (model: string, style?: string) => {
  const name = MODEL_LABELS[model] ?? model;
  return style ? `${name} · ${style}` : name;
};

export const LINE_COLORS = [
  "#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c",
  "#0891b2", "#be185d", "#65a30d", "#4f46e5", "#b45309",
];
