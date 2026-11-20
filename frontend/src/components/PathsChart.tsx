"use client";

import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getPaths, type OptionRequest } from "@/lib/api";
import { fmt, LINE_COLORS } from "@/lib/format";
import { useRequest } from "@/lib/useRequest";
import Panel from "./Panel";

const N_DISPLAY = 20;

export default function PathsChart({ request }: { request: OptionRequest }) {
  const body = { ...request, n_display: N_DISPLAY, n_steps: request.n_steps ?? 100 };
  const { data, error, loading } = useRequest(JSON.stringify(["paths", body]), () => getPaths(body));

  const rows = data?.times.map((t, i) => {
    const row: Record<string, number> = { t };
    data.paths.forEach((path, j) => (row[`p${j}`] = path[i]));
    return row;
  });

  return (
    <Panel
      title="Simulated price paths"
      subtitle={`${N_DISPLAY} risk-neutral GBM paths. The dashed lines are the strike${data?.barrier ? " and the barrier" : ""}.`}
      loading={loading}
      error={error}
    >
      {data && rows && (
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ top: 10, right: 70, bottom: 20, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="t"
                type="number"
                domain={[0, "dataMax"]}
                tickFormatter={(v) => Number(v).toFixed(2)}
                label={{ value: "Time (years)", position: "insideBottom", offset: -10 }}
              />
              <YAxis domain={["auto", "auto"]} tickFormatter={(v) => Number(v).toFixed(0)} />
              <Tooltip
                formatter={(v) => fmt(Number(v), 2)}
                labelFormatter={(v) => `t = ${fmt(Number(v), 3)}`}
                itemSorter={(item) => -Number(item.value)}
              />
              <ReferenceLine
                y={data.strike}
                stroke="#0f172a"
                strokeDasharray="6 4"
                strokeWidth={2}
                label={{ value: `K ${data.strike}`, position: "right", fontSize: 12, fill: "#0f172a" }}
              />
              {data.barrier != null && (
                <ReferenceLine
                  y={data.barrier}
                  stroke="#dc2626"
                  strokeDasharray="6 4"
                  strokeWidth={2}
                  ifOverflow="extendDomain"
                  label={{ value: `B ${data.barrier}`, position: "right", fontSize: 12, fill: "#dc2626" }}
                />
              )}
              {data.paths.map((_, j) => (
                <Line
                  key={j}
                  dataKey={`p${j}`}
                  name={`Path ${j + 1}`}
                  stroke={LINE_COLORS[j % LINE_COLORS.length]}
                  dot={false}
                  strokeWidth={1.2}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Panel>
  );
}
