import React from "react";

export function Stat({ label, value, unit, hint }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}<span className="stat-unit">{unit}</span></div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  );
}

export function Panel({ title, note, children }) {
  return (
    <section className="panel">
      <h3>{title}</h3>
      {note && <p className="note">{note}</p>}
      <div className="chart">{children}</div>
    </section>
  );
}

export function Status({ loading, error }) {
  if (loading) return <p className="status">Loading data…</p>;
  if (error) return <p className="status err">Couldn’t load data: {error}. Check that the backend is running and the Elexon data snapshot exists.</p>;
  return null;
}
