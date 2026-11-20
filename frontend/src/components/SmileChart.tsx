"use client";

import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ApiError, getImpliedVol, getVolSurface, type ImpliedVolResponse, type OptionRequest } from "@/lib/api";
import { fmt, LINE_COLORS, modelLabel, pct } from "@/lib/format";
import { useRequest } from "@/lib/useRequest";
import Panel from "./Panel";

export default function SmileChart({ request }: { request: OptionRequest }) {
  const [skewInput, setSkewInput] = useState("-0.15");
  const skew = Number(skewInput);
  const surfaceBody = {
    spot: request.spot,
    rate: request.rate,
    option_type: request.option_type,
    atm_vol: request.volatility,
    skew: Number.isFinite(skew) ? skew : -0.15,
  };
  const { data, error, loading } = useRequest(JSON.stringify(["surface", surfaceBody]), () =>
    getVolSurface(surfaceBody),
  );

  const rows = data?.strikes.map((strike, i) => {
    const row: Record<string, number> = { strike };
    data.surface.forEach((s) => (row[`T${s.maturity}`] = s.smile[i].implied_vol));
    return row;
  });

  return (
    <div className="space-y-4">
      <Panel
        title="Implied volatility smile"
        subtitle="Synthetic market prices from σ(K, T) = σ_ATM + (skew / √T)·ln(K/S), inverted with Brent's method. Shorter maturities have steeper smiles."
        loading={loading}
        error={error}
      >
        <label className="mb-3 flex items-center gap-2 text-sm">
          <span className="font-medium text-slate-700">Skew</span>
          <input
            type="number"
            step="0.05"
            value={skewInput}
            onChange={(e) => setSkewInput(e.target.value)}
            className="w-24 rounded-md border border-slate-300 px-2 py-1"
          />
          <span className="text-slate-500">ATM vol is {pct(request.volatility, 1)} (from the form)</span>
        </label>
        {data && rows && (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={rows} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="strike"
                  type="number"
                  domain={["dataMin", "dataMax"]}
                  label={{ value: "Strike", position: "insideBottom", offset: -10 }}
                />
                <YAxis domain={["auto", "auto"]} tickFormatter={(v) => pct(Number(v), 0)} />
                <Tooltip formatter={(v) => pct(Number(v))} labelFormatter={(v) => `K = ${v}`} />
                <Legend verticalAlign="top" />
                {data.surface.map((s, j) => (
                  <Line
                    key={s.maturity}
                    dataKey={`T${s.maturity}`}
                    name={`T = ${s.maturity}y`}
                    stroke={LINE_COLORS[j % LINE_COLORS.length]}
                    strokeWidth={2}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Panel>
      <ImpliedVolCalculator request={request} />
    </div>
  );
}

function ImpliedVolCalculator({ request }: { request: OptionRequest }) {
  const [marketPrice, setMarketPrice] = useState("10");
  const [result, setResult] = useState<ImpliedVolResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const solve = async () => {
    setBusy(true);
    setError(null);
    setResult(null);
    const { volatility: _ignored, ...inputs } = request;
    void _ignored;
    try {
      setResult(await getImpliedVol({ ...inputs, market_price: Number(marketPrice) }));
    } catch (err) {
      setError(
        err instanceof ApiError && err.fieldErrors.market_price
          ? `Market price: ${err.fieldErrors.market_price}`
          : err instanceof Error ? err.message : String(err),
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel
      title="Implied volatility calculator"
      subtitle={`Solves for σ so the ${modelLabel(request.model, request.style)} price matches the market price. Other inputs come from the form.`}
    >
      <form
        className="flex flex-wrap items-end gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          void solve();
        }}
      >
        <label className="text-sm">
          <span className="mb-1 block font-medium text-slate-700">Market price</span>
          <input
            type="number"
            step="any"
            value={marketPrice}
            onChange={(e) => setMarketPrice(e.target.value)}
            className="w-32 rounded-md border border-slate-300 px-2 py-1.5"
          />
        </label>
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-60"
        >
          {busy ? "Solving…" : "Solve for σ"}
        </button>
        {result && (
          <p className="text-sm">
            Implied volatility: <span className="font-semibold">{pct(result.implied_vol)}</span>{" "}
            <span className="text-slate-500">({fmt(result.implied_vol, 6)})</span>
          </p>
        )}
      </form>
      {error && <p role="alert" className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
    </Panel>
  );
}
