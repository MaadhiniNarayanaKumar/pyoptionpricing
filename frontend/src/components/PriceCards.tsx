import type { GreeksResponse, PriceResponse } from "@/lib/api";
import { fmt, modelLabel } from "@/lib/format";

const GREEKS: { key: keyof GreeksResponse["greeks"]; label: string; note: string }[] = [
  { key: "delta", label: "Delta Δ", note: "∂V/∂S" },
  { key: "gamma", label: "Gamma Γ", note: "∂²V/∂S²" },
  { key: "vega", label: "Vega ν", note: "per unit σ" },
  { key: "theta", label: "Theta Θ", note: "per year" },
  { key: "rho", label: "Rho ρ", note: "per unit r" },
];

export default function PriceCards({ price, greeks }: {
  price: PriceResponse;
  greeks: GreeksResponse;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 sm:col-span-3 lg:col-span-1">
        <p className="text-xs font-medium text-blue-700">{modelLabel(price.model, price.style)}</p>
        <p className="mt-1 text-2xl font-semibold text-slate-900">{fmt(price.price)}</p>
        {price.standard_error != null && (
          <p className="text-xs text-slate-600">± {fmt(price.standard_error)} (1 s.e.)</p>
        )}
      </div>
      {GREEKS.map(({ key, label, note }) => (
        <div key={key} className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-xs font-medium text-slate-500">{label}</p>
          <p className="mt-1 text-xl font-semibold text-slate-900">{fmt(greeks.greeks[key])}</p>
          <p className="text-xs text-slate-500">{note}</p>
        </div>
      ))}
    </div>
  );
}
