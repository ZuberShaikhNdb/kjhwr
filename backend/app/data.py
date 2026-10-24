"""Data access: snapshot (preferred) -> live Elexon fetch (cached) -> demo (explicit only)."""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from functools import lru_cache

import pandas as pd

from . import config
from .demo import make_demo
from .elexon import fetch_actuals, fetch_forecasts

ACT_FILE = "actuals.csv"
FC_FILE = "forecasts.csv"


def _window():
    """Fetch window covering every delivery day in scope plus the forecasts that precede them."""
    first = config.DELIVERY_START - timedelta(days=3)
    last = config.DELIVERY_END + timedelta(days=1)
    return first, last


def fetch_and_save(directory=None):
    """Download from Elexon and write the CSV snapshot. Used by scripts/fetch_data.py and as a runtime fallback."""
    directory = directory or config.SNAPSHOT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    first, last = _window()
    act = fetch_actuals(first, last)
    fc = fetch_forecasts(
        datetime.combine(first, time.min, tzinfo=timezone.utc),
        datetime.combine(last, time.min, tzinfo=timezone.utc),
    )
    act.to_csv(directory / ACT_FILE, index=False)
    fc.to_csv(directory / FC_FILE, index=False)
    return act, fc


def _read_snapshot(directory):
    act = pd.read_csv(directory / ACT_FILE, parse_dates=["startTime"])
    fc = pd.read_csv(directory / FC_FILE, parse_dates=["startTime", "publishTime"])
    for df, cols in ((act, ["startTime"]), (fc, ["startTime", "publishTime"])):
        for c in cols:
            df[c] = pd.to_datetime(df[c], utc=True)
    return act, fc


@lru_cache(maxsize=1)
def get_data():
    """Returns (actuals, forecasts, mode) where mode is 'demo' | 'snapshot' | 'live'."""
    if config.DEMO_MODE:
        act, fc = make_demo()
        return act, fc, "demo"
    d = config.SNAPSHOT_DIR
    if (d / ACT_FILE).exists() and (d / FC_FILE).exists():
        act, fc = _read_snapshot(d)
        return act, fc, "snapshot"
    try:
        act, fc = fetch_and_save()
        return act, fc, "live"
    except OSError:  # read-only filesystem (serverless): fetch again without saving
        first, last = _window()
        act = fetch_actuals(first, last)
        fc = fetch_forecasts(
            datetime.combine(first, time.min, tzinfo=timezone.utc),
            datetime.combine(last, time.min, tzinfo=timezone.utc),
        )
        return act, fc, "live"
