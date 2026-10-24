import React, { useState } from "react";
import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useApi } from "./hooks.js";
import { fmtDay, fmtTs, gw, mw } from "./api.js";
import { Panel, Stat, Status } from "./ui.jsx";

export default function DecisionTab({ meta, cutoff }) {
  const [date, setDate] = useState(meta.delivery_dates[14]);
  const [showActual, setShowActual] = useState(true);
  const { data, error, loading } = useApi(`/decision/${date}?cutoff=${cutoff}`);

  const rows = (data?.rows || []).map((r) => ({
    ...r,
    band: r.lower != null ? [r.lower, r.upper] : null,
    base: r.lower,
    span: r.lower != null ? r.upper - r.lower : null,
  }));
  const band = data?.band;
  const s = data?.forecast_summary;
  const m = data?.day_metrics;

  return (
    <>
      <div className="toolbar">
        <label>
          Delivery day
          <select value={date} onChange={(e) => setDate(e.target.value)}>
            {meta.delivery_dates.map((d) => <option key={d} value={d}>{fmtDay(d)} 2026</option>)}
          </select>
        </label>
        <label className="check">
          <input type="checkbox" checked={showActual} onChange={(e) => setShowActual(e.target.checked)} />
          Show what actually happened
        </label>
      </div>

      <Status loading={loading} error={error} />
      {data && (
        <>
          <p className="lead">
            To buy for <b>{fmtDay(date)}</b>, the decision is made by <b>{data.decision_deadline_local} (UK)</b>.
            The newest wind forecast available then was published <b>{fmtTs(data.latest_publish_time)}</b>.
          </p>

          <div className="stats">
            <Stat label="Average forecast wind" value={gw(s.mean_mw)} unit=" GW" />
            <Stat label="Peak forecast" value={gw(s.peak_mw)} unit=" GW" />
            <Stat label="Lowest forecast" value={gw(s.min_mw)} unit=" GW" />
            <Stat label="Forecast energy" value={mw(s.energy_mwh)} unit=" MWh" />
          </div>

          <Panel
            title="Wind generation: forecast available on the day before"
            note={band?.q05 != null
              ? `Shaded band: 90% of past errors fall inside it (based on ${band.days} ${band.basis === "prior days" ? "earlier days" : "days"}). Buy the gap between demand and the lower edge if you want to be safe against low wind.`
              : "Not enough history to draw an error band."}
          >
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={rows} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                <CartesianGrid stroke="var(--grid)" vertical={false} />
                <XAxis dataKey="local_time" interval={5} tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => `${v / 1000}`} tick={{ fontSize: 12 }} unit=" GW" width={58} />
                <Tooltip content={<DecisionTip showActual={showActual} />} />
                <Legend verticalAlign="top" height={30} />
                <Area dataKey="base" stackId="b" stroke="none" fill="transparent" legendType="none" isAnimationActive={false} />
                <Area dataKey="span" stackId="b" stroke="none" fill="var(--forecast)" fillOpacity={0.16} name="90% error band" isAnimationActive={false} />
                <Line dataKey="forecast" name="Forecast" stroke="var(--forecast)" strokeWidth={2.5} dot={false} isAnimationActive={false} />
                {showActual && <Line dataKey="actual" name="Actual" stroke="var(--actual)" strokeWidth={2} dot={false} isAnimationActive={false} />}
              </ComposedChart>
            </ResponsiveContainer>
          </Panel>

          {showActual && m?.n > 0 && (
            <div className="stats">
              <Stat label="Mean absolute error this day" value={mw(m.mae)} unit=" MW" />
              <Stat label="Average bias" value={`${m.bias > 0 ? "+" : ""}${mw(m.bias)}`} unit=" MW" hint={m.bias > 0 ? "forecast too high" : "forecast too low"} />
              <Stat label="Worst half-hour miss" value={mw(m.max_abs)} unit=" MW" />
              <Stat label="Error as % of output" value={m.wape_pct ?? "–"} unit="%" />
            </div>
          )}
        </>
      )}
    </>
  );
}

function DecisionTip({ active, payload, label, showActual }) {
  if (!active || !payload?.length) return null;
  const r = payload[0].payload;
  return (
    <div className="tip">
      <b>{label}</b>
      <div>Forecast: {mw(r.forecast)} MW</div>
      {showActual && <div>Actual: {mw(r.actual)} MW</div>}
      {showActual && r.error != null && <div>Error: {r.error > 0 ? "+" : ""}{mw(r.error)} MW</div>}
      {r.lower != null && <div className="muted">Range: {mw(r.lower)}–{mw(r.upper)} MW</div>}
      <div className="muted">Lead time {r.horizon_h.toFixed(1)} h</div>
    </div>
  );
}
