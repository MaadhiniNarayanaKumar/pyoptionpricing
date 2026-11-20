"use client";

import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getPayoff, type OptionRequest } from "@/lib/api";
import { fmt } from "@/lib/format";
import { useRequest } from "@/lib/useRequest";
import Panel from "./Panel";

export default function PayoffChart({ request }: { request: OptionRequest }) {
  const { data, error, loading } = useRequest(JSON.stringify(["payoff", request]), () =>
    getPayoff(request),
  );

  return (
    <Panel
      title="Payoff at maturity"
      subtitle={
        data
          ? `Vanilla ${request.option_type} payoff, and profit after a premium of ${fmt(data.premium)} (the chosen model's price).`
          : undefined
      }
      loading={loading}
      error={error}
    >
      {data && (
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.points} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="spot"
                type="number"
                domain={["dataMin", "dataMax"]}
                tickFormatter={(v) => Number(v).toFixed(0)}
                label={{ value: "Spot at maturity", position: "insideBottom", offset: -10 }}
              />
              <YAxis tickFormatter={(v) => Number(v).toFixed(0)} />
              <Tooltip formatter={(v) => fmt(Number(v), 2)} labelFormatter={(v) => `S_T = ${fmt(Number(v), 2)}`} />
              <Legend verticalAlign="top" />
              <ReferenceLine y={0} stroke="#64748b" />
              <ReferenceLine x={data.strike} stroke="#94a3b8" strokeDasharray="4 4" label="K" />
              <Line type="linear" dataKey="payoff" name="Payoff" stroke="#2563eb" dot={false} strokeWidth={2} />
              <Line type="linear" dataKey="profit" name="Profit" stroke="#16a34a" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Panel>
  );
}
