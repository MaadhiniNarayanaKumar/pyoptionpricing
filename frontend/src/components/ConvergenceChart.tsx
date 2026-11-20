"use client";

import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getConvergence, type OptionRequest } from "@/lib/api";
import { fmt } from "@/lib/format";
import { useRequest } from "@/lib/useRequest";
import Panel from "./Panel";

export default function ConvergenceChart({ request }: { request: OptionRequest }) {
  const { data, error, loading } = useRequest(JSON.stringify(["convergence", request]), () =>
    getConvergence(request),
  );
  const american = request.model === "binomial" && request.style === "american";
  const exotic = request.model === "asian" || request.model === "barrier";
  const exoticNote = exotic ? " Shown for the vanilla European contract with the same inputs." : "";

  const mcRows = data?.monte_carlo.points.map((p) => ({
    ...p,
    upper: p.price + 2 * p.standard_error,
    lower: p.price - 2 * p.standard_error,
  }));

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Panel
        title={`Binomial convergence${american ? " (American)" : ""}`}
        subtitle={
          american
            ? "The red line is the European Black-Scholes price. The gap that remains is the early-exercise premium."
            : `The tree price oscillates towards the Black-Scholes price (red) as steps grow.${exoticNote}`
        }
        loading={loading}
        error={error}
      >
        {data && (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.binomial.points} margin={{ top: 10, right: 80, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="steps"
                  type="number"
                  scale="log"
                  domain={["dataMin", "dataMax"]}
                  ticks={data.binomial.points.map((p) => p.steps)}
                  label={{ value: "Tree steps (log scale)", position: "insideBottom", offset: -10 }}
                />
                <YAxis domain={["auto", "auto"]} tickFormatter={(v) => Number(v).toFixed(2)} />
                <Tooltip formatter={(v) => fmt(Number(v))} labelFormatter={(v) => `${v} steps`} />
                <Legend verticalAlign="top" />
                <ReferenceLine
                  y={data.binomial.black_scholes}
                  stroke="#dc2626"
                  strokeDasharray="4 4"
                  ifOverflow="extendDomain"
                  label={{ value: `BS ${fmt(data.binomial.black_scholes)}`, position: "right", fontSize: 11, fill: "#dc2626" }}
                />
                <Line dataKey="price" name="Binomial price" stroke="#2563eb" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Panel>

      <Panel
        title="Monte Carlo convergence"
        subtitle={`European Monte Carlo price with a ± 2 standard error band. Red is Black-Scholes.${exoticNote}`}
        loading={loading}
        error={error}
      >
        {data && mcRows && (
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mcRows} margin={{ top: 10, right: 80, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="n_paths"
                  type="number"
                  scale="log"
                  domain={["dataMin", "dataMax"]}
                  ticks={mcRows.map((p) => p.n_paths)}
                  tickFormatter={(v) => (v >= 1000 ? `${v / 1000}k` : String(v))}
                  label={{ value: "Paths (log scale)", position: "insideBottom", offset: -10 }}
                />
                <YAxis domain={["auto", "auto"]} tickFormatter={(v) => Number(v).toFixed(2)} />
                <Tooltip formatter={(v) => fmt(Number(v))} labelFormatter={(v) => `${v} paths`} />
                <Legend verticalAlign="top" />
                <ReferenceLine
                  y={data.monte_carlo.black_scholes}
                  stroke="#dc2626"
                  strokeDasharray="4 4"
                  ifOverflow="extendDomain"
                  label={{ value: `BS ${fmt(data.monte_carlo.black_scholes)}`, position: "right", fontSize: 11, fill: "#dc2626" }}
                />
                <Line dataKey="price" name="MC price" stroke="#2563eb" strokeWidth={2} />
                <Line dataKey="upper" name="+2 s.e." stroke="#94a3b8" strokeDasharray="3 3" dot={false} />
                <Line dataKey="lower" name="−2 s.e." stroke="#94a3b8" strokeDasharray="3 3" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Panel>
    </div>
  );
}
