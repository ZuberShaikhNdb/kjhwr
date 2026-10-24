"""Thin client for the Elexon BMRS open-data API (no API key required).

Only two datasets are used:
  * FUELHH  - half-hourly actual generation by fuel type (we keep fuelType == WIND)
  * WINDFOR - national wind generation forecasts (each row has startTime + publishTime)
"""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone

import httpx
import pandas as pd

from .config import ELEXON_BASE


def _get_json(client: httpx.Client, path: str, params: dict, retries: int = 4):
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = client.get(f"{ELEXON_BASE}{path}", params=params, timeout=60)
            r.raise_for_status()
            body = r.json()
            return body["data"] if isinstance(body, dict) and "data" in body else body
        except Exception as exc:  # noqa: BLE001 - retry on any transport/parse error
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Elexon request failed for {path} {params}: {last}")


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_actuals(start: date, end: date) -> pd.DataFrame:
    """Actual wind generation (MW) per half hour for settlement dates start..end inclusive."""
    rows: list[dict] = []
    with httpx.Client() as client:
        cur = start
        while cur <= end:  # chunk by 7 days to stay inside API range limits
            chunk_end = min(cur + timedelta(days=6), end)
            rows += _get_json(
                client,
                "/datasets/FUELHH/stream",
                {
                    "settlementDateFrom": cur.isoformat(),
                    "settlementDateTo": chunk_end.isoformat(),
                    "fuelType": "WIND",
                    "format": "json",
                },
            )
            cur = chunk_end + timedelta(days=1)
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["startTime", "generation"])
    df = df[df["fuelType"] == "WIND"].copy()
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    if "publishTime" in df:  # keep the latest published value if a slot appears twice
        df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
        df = df.sort_values("publishTime")
    df = df.drop_duplicates("startTime", keep="last").sort_values("startTime")
    return df[["startTime", "generation"]].reset_index(drop=True)


def fetch_forecasts(publish_from: datetime, publish_to: datetime) -> pd.DataFrame:
    """All WINDFOR forecast rows published in [publish_from, publish_to]."""
    rows: list[dict] = []
    with httpx.Client() as client:
        cur = publish_from
        while cur < publish_to:
            nxt = min(cur + timedelta(days=2), publish_to)
            rows += _get_json(
                client,
                "/datasets/WINDFOR/stream",
                {"publishDateTimeFrom": _iso(cur), "publishDateTimeTo": _iso(nxt), "format": "json"},
            )
            cur = nxt
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["publishTime", "startTime", "generation"])
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df = df.drop_duplicates(["publishTime", "startTime"], keep="last")
    return df[["publishTime", "startTime", "generation"]].sort_values(["publishTime", "startTime"]).reset_index(drop=True)
