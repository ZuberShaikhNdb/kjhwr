import React, { useState } from "react";
import { useApi } from "./hooks.js";
import { Status } from "./ui.jsx";
import DecisionTab from "./DecisionTab.jsx";
import AccuracyTab from "./AccuracyTab.jsx";
import HorizonTab from "./HorizonTab.jsx";

const TABS = [
  ["decision", "Tomorrow’s wind"],
  ["accuracy", "Forecast accuracy"],
  ["horizon", "Accuracy vs lead time"],
];

export default function App() {
  const { data: meta, error, loading } = useApi("/meta");
  const [tab, setTab] = useState("decision");
  const [cutoff, setCutoff] = useState(null);
  const activeCutoff = cutoff || meta?.default_cutoff;

  return (
    <div className="app">
      {meta?.mode === "demo" && <div className="banner">Demo mode: synthetic data, not real Elexon values.</div>}
      <header>
        <h1>Wind Forecast Monitor</h1>
        <p>GB national wind generation · day-ahead purchasing · January 2026 · source: Elexon BMRS (FUELHH, WINDFOR)</p>
      </header>

      <Status loading={loading} error={error} />
      {meta && (
        <>
          <div className="controls">
            <nav role="tablist" aria-label="Views">
              {TABS.map(([id, label]) => (
                <button key={id} role="tab" aria-selected={tab === id} className={tab === id ? "on" : ""} onClick={() => setTab(id)}>
                  {label}
                </button>
              ))}
            </nav>
            <label className="cutoff">
              Decision deadline (UK, day before)
              <select value={activeCutoff} onChange={(e) => setCutoff(e.target.value)}>
                {meta.cutoff_options.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </label>
          </div>
          <main>
            {tab === "decision" && <DecisionTab meta={meta} cutoff={activeCutoff} />}
            {tab === "accuracy" && <AccuracyTab cutoff={activeCutoff} />}
            {tab === "horizon" && <HorizonTab cutoff={activeCutoff} />}
          </main>
          <footer>Error = forecast − actual. Forecast used = latest one published before the deadline. Actuals are shown only to back-test past decisions.</footer>
        </>
      )}
    </div>
  );
}
