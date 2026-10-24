"""Pure analysis functions (no I/O) so they are easy to unit-test.

Key concept - the *decision forecast*:
  For a delivery slot at time t on delivery date D, the buyer decides on D-1 at `cutoff` (UK local time).
  The forecast they can use is the most recent one with publishTime <= cutoff.
  Sign convention: error = forecast - actual  (positive = forecast too high = risk of under-buying).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import TIMEZONE


def _f(x, nd=1):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), nd)


def cutoff_utc(start_times: pd.Series, cutoff: str) -> pd.Series:
    """Decision deadline (UTC) for each slot: (local delivery date - 1 day) at `cutoff` local time."""
    hh, mm = (int(p) for p in cutoff.split(":"))
    local_day = start_times.dt.tz_convert(TIMEZONE).dt.tz_localize(None).dt.normalize()
    naive = local_day - pd.Timedelta(days=1) + pd.Timedelta(hours=hh, minutes=mm)
    return naive.dt.tz_localize(TIMEZONE, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")


def decision_forecasts(fc: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """Latest forecast available at the decision cutoff, one row per target slot."""
    d = fc.copy()
    d["cutoff"] = cutoff_utc(d["startTime"], cutoff)
    d = d[d["publishTime"] <= d["cutoff"]]
    d = d.sort_values("publishTime").groupby("startTime", as_index=False).tail(1)
    d["horizon_h"] = (d["startTime"] - d["publishTime"]).dt.total_seconds() / 3600
    return d.rename(columns={"generation": "forecast"})[["startTime", "publishTime", "forecast", "horizon_h"]]


def build_eval(fc: pd.DataFrame, act: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """Decision forecast joined with actuals, tagged with local delivery date / time."""
    d = decision_forecasts(fc, cutoff)
    a = act[["startTime", "generation"]].rename(columns={"generation": "actual"})
    m = d.merge(a, on="startTime", how="left")
    m["error"] = m["forecast"] - m["actual"]
    local = m["startTime"].dt.tz_convert(TIMEZONE)
    m["delivery_date"] = local.dt.strftime("%Y-%m-%d")
    m["local_time"] = local.dt.strftime("%H:%M")
    return m.sort_values("startTime").reset_index(drop=True)


def metrics(df: pd.DataFrame) -> dict:
    x = df.dropna(subset=["actual", "forecast"])
    if x.empty:
        return {"n": 0}
    e, ae = x["error"], x["error"].abs()
    total_actual = x["actual"].sum()
    return {
        "n": int(len(x)),
        "mae": _f(ae.mean()),
        "rmse": _f(np.sqrt((e**2).mean())),
        "bias": _f(e.mean()),
        "wape_pct": _f(100 * ae.sum() / total_actual, 2) if total_actual > 0 else None,
        "p50_abs": _f(ae.quantile(0.5)),
        "p90_abs": _f(ae.quantile(0.9)),
        "p95_abs": _f(ae.quantile(0.95)),
        "max_abs": _f(ae.max()),
        "mean_actual": _f(x["actual"].mean()),
        "over_forecast_pct": _f(100 * (e > 0).mean()),
    }


def daily_metrics(df: pd.DataFrame) -> list[dict]:
    out = []
    for date, g in df.dropna(subset=["actual"]).groupby("delivery_date"):
        m = metrics(g)
        out.append({"date": date, **{k: m.get(k) for k in ("mae", "rmse", "bias", "wape_pct", "mean_actual")}})
    return out


def hourly_metrics(df: pd.DataFrame) -> list[dict]:
    out = []
    for t, g in df.dropna(subset=["actual"]).groupby("local_time"):
        ae = g["error"].abs()
        out.append({"time": t, "mae": _f(ae.mean()), "bias": _f(g["error"].mean()), "p90_abs": _f(ae.quantile(0.9))})
    return out


def error_histogram(df: pd.DataFrame, width: int = 250) -> list[dict]:
    e = df.dropna(subset=["error"])["error"].to_numpy()
    if e.size == 0:
        return []
    lo, hi = np.floor(e.min() / width) * width, np.ceil(e.max() / width) * width + width
    edges = np.arange(lo, hi + 1, width)
    counts, _ = np.histogram(e, bins=edges)
    return [{"bin": int(edges[i] + width / 2), "count": int(c)} for i, c in enumerate(counts)]


def error_band(ev: pd.DataFrame, before_date: str | None) -> dict:
    """Empirical 90% interval of (forecast - actual) from days strictly before `before_date`
    (no look-ahead). Falls back to all available history if fewer than 2 prior days exist."""
    known = ev.dropna(subset=["actual"])
    prior = known[known["delivery_date"] < before_date] if before_date else known
    basis = "prior days"
    if prior["delivery_date"].nunique() < 2:
        prior, basis = known, "all days in scope"
    if prior.empty:
        return {"lo": None, "hi": None, "basis": None, "days": 0}
    return {
        "q05": _f(prior["error"].quantile(0.05)),
        "q95": _f(prior["error"].quantile(0.95)),
        "basis": basis,
        "days": int(prior["delivery_date"].nunique()),
    }


def horizon_metrics(fc: pd.DataFrame, act: pd.DataFrame, start_date: str, end_date: str, bucket_h: int = 3, max_h: int = 96):
    """Accuracy of *every* forecast row (not just decision forecasts) grouped by lead time."""
    a = act[["startTime", "generation"]].rename(columns={"generation": "actual"})
    m = fc.merge(a, on="startTime", how="inner")
    local_date = m["startTime"].dt.tz_convert(TIMEZONE).dt.strftime("%Y-%m-%d")
    m = m[(local_date >= start_date) & (local_date <= end_date)].copy()
    m["h"] = (m["startTime"] - m["publishTime"]).dt.total_seconds() / 3600
    m = m[(m["h"] >= 0) & (m["h"] <= max_h)]
    m["error"] = m["generation"] - m["actual"]
    m["bucket"] = (np.floor(m["h"] / bucket_h) * bucket_h).astype(int)
    out = []
    for b, g in m.groupby("bucket"):
        ae = g["error"].abs()
        out.append({"horizon_h": int(b), "mae": _f(ae.mean()), "rmse": _f(np.sqrt((g["error"] ** 2).mean())),
                    "bias": _f(g["error"].mean()), "p90_abs": _f(ae.quantile(0.9)), "n": int(len(g))})
    return out
