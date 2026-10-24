import React from "react";
import { CartesianGrid, ComposedChart, Legend, Line, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useApi } from "./hooks.js";
import { mw } from "./api.js";
import { Panel, Status } from "./ui.jsx";

export default function HorizonTab({ cutoff }) {
  const { data, error, loading } = useApi(`/horizon?cutoff=${cutoff}`);
  const [lo, hi] = data?.decision_window_h || [];
  return (
    <>
      <Status loading={loading} error={error} />
      {data && (
        <>
          <p className="lead">
            How does accuracy change with lead time (how long before the target half-hour the forecast was published)? Day-ahead decisions
            use forecasts with a lead time of roughly <b>{Math.round(lo)}–{Math.round(hi)} hours</b>, the shaded zone.
          </p>
          <Panel title="Error versus forecast lead time" note="Every forecast issued for January 2026, grouped into 3-hour lead-time buckets.">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data.buckets} margin={{ top: 8, right: 8, left: -8, bottom: 16 }}>
                <CartesianGrid stroke="var(--grid)" vertical={false} />
                <XAxis dataKey="horizon_h" type="number" domain={[0, 96]} ticks={[0, 12, 24, 36, 48, 60, 72, 84, 96]} tick={{ fontSize: 12 }} unit=" h" label={{ value: "Lead time", position: "insideBottom", offset: -8, fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${v / 1000}`} unit=" GW" width={58} />
                <Tooltip labelFormatter={(h) => `Lead time ${h}–${h + 3} h`} formatter={(v, n) => [`${mw(v)} MW`, n]} />
                <Legend verticalAlign="top" height={30} />
                <ReferenceArea x1={lo} x2={hi} fill="var(--forecast)" fillOpacity={0.12} />
                <Line dataKey="mae" name="Mean absolute error" stroke="var(--forecast)" strokeWidth={2.5} dot={false} isAnimationActive={false} />
                <Line dataKey="p90_abs" name="P90 absolute error" stroke="var(--actual)" strokeWidth={2} strokeDasharray="5 4" dot={false} isAnimationActive={false} />
                <Line dataKey="bias" name="Bias" stroke="var(--ink)" strokeWidth={1.5} dot={false} isAnimationActive={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </Panel>
        </>
      )}
    </>
  );
}
