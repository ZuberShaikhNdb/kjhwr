"""Synthetic data generator - ONLY for offline development and unit tests.
The API reports `mode: demo` so the UI shows a visible banner when this is used."""
from __future__ import annotations

import numpy as np
import pandas as pd


def make_demo(start="2025-12-29", end="2026-02-01", seed=7):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, end, freq="30min", tz="UTC", inclusive="left")
    n = len(idx)
    # slow AR(1) "weather" process scaled to a plausible GB wind range (0-20 GW)
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.995 * x[i - 1] + rng.normal(0, 0.06)
    actual = np.clip(9000 + 4500 * x / x.std() * 0.9, 300, 20000)
    act = pd.DataFrame({"startTime": idx, "generation": actual})

    rows = []
    pubs = pd.date_range(idx[0], idx[-1] - pd.Timedelta(hours=1), freq="1h", tz="UTC")
    for p in pubs:
        tgt = idx[(idx > p) & (idx <= p + pd.Timedelta(hours=48))]
        h = (tgt - p).total_seconds() / 3600
        base = actual[idx.get_indexer(tgt)]
        noise = rng.normal(0, 250 + 55 * h)  # error grows with horizon
        rows.append(pd.DataFrame({"publishTime": p, "startTime": tgt, "generation": np.clip(base + noise - 80, 0, None)}))
    fc = pd.concat(rows, ignore_index=True)
    return act, fc
