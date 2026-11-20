"use client";

import { Bar, BarChart, CartesianGrid, ErrorBar, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { compareModels, type OptionRequest } from "@/lib/api";
import { fmt, modelLabel } from "@/lib/format";
import { useRequest } from "@/lib/useRequest";
import Panel from "./Panel";

export default function CompareView({ request }: { request: OptionRequest }) {
  const { data, error, loading } = useRequest(JSON.stringify(["compare", request]), () =>
    compareModels(request),
  );

  // Recharts forwards row fields to SVG elements, so the API's "style" field must not be in a row.
  const rows = (data?.results ?? []).map(({ style, ...r }) => ({
    ...r,
    label: modelLabel(r.model, style),
    band: r.standard_error != null ? 2 * r.standard_error : 0,
  }));

  return (
    <Panel
      title="Model comparison"
      subtitle="The same contract priced by every model. Barrier appears when a barrier level is set (choose the Barrier model)."
      loading={loading}
      error={error}
    >
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={70} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => fmt(Number(v))} />
            <Bar dataKey="price" fill="#2563eb" name="Price">
              <ErrorBar dataKey="band" width={6} stroke="#0f172a" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mb-2 text-xs text-slate-500">Error bars on simulated models show ± 2 standard errors.</p>

      <div className="overflow-x-auto">
        <table className="w-full text-right text-sm">
          <thead className="border-b text-xs uppercase text-slate-500">
            <tr>
              <th className="py-2 text-left">Model</th>
              <th>Price</th>
              <th>Std. error</th>
              <th>Delta</th>
              <th>Gamma</th>
              <th>Vega</th>
              <th>Theta</th>
              <th>Rho</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.label} className="border-b last:border-0">
                <td className="py-2 text-left font-medium">{r.label}</td>
                <td>{fmt(r.price)}</td>
                <td>{fmt(r.standard_error)}</td>
                <td>{fmt(r.greeks.delta)}</td>
                <td>{fmt(r.greeks.gamma)}</td>
                <td>{fmt(r.greeks.vega, 3)}</td>
                <td>{fmt(r.greeks.theta, 3)}</td>
                <td>{fmt(r.greeks.rho, 3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
