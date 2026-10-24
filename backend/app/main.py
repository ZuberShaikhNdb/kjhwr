"""FastAPI application: JSON API under /api + serves the built React app (if present)."""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import analysis, config
from .data import get_data

app = FastAPI(title="Wind Forecast Monitor", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


def _load():
    try:
        return get_data()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, f"Could not load Elexon data: {exc}") from exc


def _check_cutoff(cutoff: str) -> str:
    try:
        hh, mm = cutoff.split(":")
        assert 0 <= int(hh) < 24 and 0 <= int(mm) < 60
    except Exception:  # noqa: BLE001
        raise HTTPException(422, "cutoff must be HH:MM (UK local time)")
    return cutoff


def _check_date(d: str) -> str:
    try:
        parsed = date.fromisoformat(d)
    except ValueError:
        raise HTTPException(422, f"Invalid date '{d}', expected YYYY-MM-DD")
    if not (config.DELIVERY_START <= parsed <= config.DELIVERY_END):
        raise HTTPException(404, f"Delivery date must be between {config.DELIVERY_START} and {config.DELIVERY_END}")
    return d


def _eval(cutoff: str) -> pd.DataFrame:
    act, fc, _ = _load()
    ev = analysis.build_eval(fc, act, cutoff)
    return ev[(ev["delivery_date"] >= str(config.DELIVERY_START)) & (ev["delivery_date"] <= str(config.DELIVERY_END))]


def _nan_to_none(records: list[dict]) -> list[dict]:
    return [{k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()} for r in records]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def meta():
    _, _, mode = _load()
    days = [str(config.DELIVERY_START + timedelta(days=i)) for i in range((config.DELIVERY_END - config.DELIVERY_START).days + 1)]
    return {
        "mode": mode,
        "timezone": config.TIMEZONE,
        "delivery_dates": days,
        "default_cutoff": config.DEFAULT_CUTOFF,
        "cutoff_options": config.CUTOFF_OPTIONS,
        "sign_convention": "error = forecast - actual (positive = forecast above actual)",
    }


@app.get("/api/decision/{delivery_date}")
def decision(delivery_date: str, cutoff: str = Query(config.DEFAULT_CUTOFF)):
    """The forecast a buyer would have on D-1 for every half hour of `delivery_date`, with actuals (back-test)."""
    _check_date(delivery_date)
    _check_cutoff(cutoff)
    ev = _eval(cutoff)
    day = ev[ev["delivery_date"] == delivery_date]
    if day.empty:
        raise HTTPException(404, "No forecast was available at the decision cutoff for this date")
    band = analysis.error_band(ev, delivery_date)
    rows = day.assign(
        startTime=day["startTime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        publishTime=day["publishTime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )[["startTime", "local_time", "forecast", "actual", "error", "publishTime", "horizon_h"]]
    if band.get("q05") is not None:
        # actual is expected within [forecast - q95, forecast - q05] ~ 90% of the time
        rows = rows.assign(
            lower=(rows["forecast"] - band["q95"]).clip(lower=0), upper=rows["forecast"] - band["q05"]
        )
    return {
        "delivery_date": delivery_date,
        "cutoff": cutoff,
        "decision_deadline_local": f"{(date.fromisoformat(delivery_date) - timedelta(days=1)).isoformat()} {cutoff}",
        "latest_publish_time": day["publishTime"].max().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "forecast_summary": {
            "mean_mw": analysis._f(day["forecast"].mean()),
            "peak_mw": analysis._f(day["forecast"].max()),
            "min_mw": analysis._f(day["forecast"].min()),
            "energy_mwh": analysis._f(day["forecast"].sum() * 0.5, 0),
        },
        "day_metrics": analysis.metrics(day),
        "band": band,
        "rows": _nan_to_none(rows.round(1, ).to_dict("records")),
    }


@app.get("/api/accuracy")
def accuracy(cutoff: str = Query(config.DEFAULT_CUTOFF)):
    """Quantified forecast error for all January 2026 decisions."""
    _check_cutoff(cutoff)
    ev = _eval(cutoff)
    return {
        "cutoff": cutoff,
        "overall": analysis.metrics(ev),
        "daily": analysis.daily_metrics(ev),
        "by_time_of_day": analysis.hourly_metrics(ev),
        "histogram": analysis.error_histogram(ev),
    }


@app.get("/api/horizon")
def horizon(cutoff: str = Query(config.DEFAULT_CUTOFF)):
    """Error versus forecast lead time, plus the lead-time window that decisions actually use."""
    _check_cutoff(cutoff)
    act, fc, _ = _load()
    ev = _eval(cutoff)
    return {
        "buckets": analysis.horizon_metrics(fc, act, str(config.DELIVERY_START), str(config.DELIVERY_END)),
        "decision_window_h": [analysis._f(ev["horizon_h"].min()), analysis._f(ev["horizon_h"].max())],
    }


# ---- static React build (single-container deployment) ----
if config.STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=config.STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = config.STATIC_DIR / path
        return FileResponse(f if path and f.is_file() else config.STATIC_DIR / "index.html")
