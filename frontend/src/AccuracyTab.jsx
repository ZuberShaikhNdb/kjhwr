import React from "react";
import { Bar, BarChart, CartesianGrid, ComposedChart, Legend, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useApi } from "./hooks.js";
import { fmtDay, mw } from "./api.js";
import { Panel, Stat, Status } from "./ui.jsx";

const axis = { fontSize: 12 };

export default function AccuracyTab({ cutoff }) {
  const { data, error, loading } = useApi(`/accuracy?cutoff=${cutoff}`);
  const o = data?.overall;
  return (
    <>
      <Status loading={loading} error={error} />
      {data && (
        <>
          <p className="lead">
            Across all <b>{o.n.toLocaleString("en-GB")}</b> half-hours of January 2026, using the forecast that was actually available the
            day before. Errors are <i>forecast − actual</i>.
          </p>
          <div className="stats">
            <Stat label="Mean absolute error" value={mw(o.mae)} unit=" MW" hint={`${o.wape_pct}% of generation`} />
            <Stat label="Typical large miss (P90)" value={mw(o.p90_abs)} unit=" MW" hint="9 in 10 slots are better than this" />
            <Stat label="Worst case (P95)" value={mw(o.p95_abs)} unit=" MW" hint={`max ${mw(o.max_abs)} MW`} />
            <Stat label="RMSE" value={mw(o.rmse)} unit=" MW" hint="penalises big misses" />
            <Stat label="Bias" value={`${o.bias > 0 ? "+" : ""}${mw(o.bias)}`} unit=" MW" hint={`forecast too high in ${o.over_forecast_pct}% of slots`} />
          </div>

          <Panel title="Error by delivery day" note="Bars show average miss per day; the line shows whether the forecast ran high (+) or low (−).">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data.daily} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                <CartesianGrid stroke="var(--grid)" vertical={false} />
                <XAxis dataKey="date" tickFormatter={(d) => d.slice(8)} tick={axis} />
                <YAxis tick={axis} tickFormatter={(v) => `${v / 1000}`} unit=" GW" width={58} />
                <Tooltip labelFormatter={fmtDay} formatter={(v, n) => [`${mw(v)} MW`, n]} />
                <Legend verticalAlign="top" height={30} />
                <ReferenceLine y={0} stroke="var(--ink)" />
                <Bar dataKey="mae" name="Mean absolute error" fill="var(--forecast)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                <Line dataKey="bias" name="Bias" stroke="var(--actual)" strokeWidth={2} dot={{ r: 2 }} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </Panel>

          <Panel title="Error by time of day" note="Which half-hours are hardest to forecast? Use the P90 line to size a safety margin per slot.">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data.by_time_of_day} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                <CartesianGrid stroke="var(--grid)" vertical={false} />
                <XAxis dataKey="time" interval={5} tick={axis} />
                <YAxis tick={axis} tickFormatter={(v) => `${v / 1000}`} unit=" GW" width={58} />
                <Tooltip formatter={(v, n) => [`${mw(v)} MW`, n]} />
                <Legend verticalAlign="top" height={30} />
                <Line dataKey="mae" name="Mean absolute error" stroke="var(--forecast)" strokeWidth={2.5} dot={false} isAnimationActive={false} />
                <Line dataKey="p90_abs" name="P90 absolute error" stroke="var(--actual)" strokeWidth={2} dot={false} strokeDasharray="5 4" isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </Panel>

          <Panel title="How errors are distributed" note="Number of half-hours at each error size. Left of zero = forecast too low; right = too high.">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.histogram} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                <CartesianGrid stroke="var(--grid)" vertical={false} />
                <XAxis dataKey="bin" tick={axis} tickFormatter={(v) => `${v / 1000}`} unit=" GW" />
                <YAxis tick={axis} width={40} />
                <Tooltip labelFormatter={(v) => `Error around ${mw(v)} MW`} formatter={(v) => [v, "Half-hours"]} />
                <ReferenceLine x={0} stroke="var(--ink)" />
                <Bar dataKey="count" fill="var(--forecast)" isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </Panel>
        </>
      )}
    </>
  );
}
