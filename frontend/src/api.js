// Tiny fetch wrapper; same-origin in production, proxied to FastAPI by Vite in dev.
export async function api(path) {
  const res = await fetch(`/api${path}`);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch { /* ignore */ }
    throw new Error(detail);
  }
  return res.json();
}

export const mw = (v) => (v == null ? "–" : Math.round(v).toLocaleString("en-GB"));
export const gw = (v) => (v == null ? "–" : (v / 1000).toFixed(2));
export const fmtDay = (iso) =>
  new Date(iso + "T12:00:00Z").toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" });
export const fmtTs = (iso) =>
  new Date(iso).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "Europe/London" });
