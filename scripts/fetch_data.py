"""Download the Elexon data once and store it as CSV in data/snapshot/.
Run:  python scripts/fetch_data.py      (needs internet access; takes ~1-2 minutes)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.data import fetch_and_save  # noqa: E402

act, fc = fetch_and_save()
print(f"actuals:   {len(act):>7} rows  {act.startTime.min()} -> {act.startTime.max()}")
print(f"forecasts: {len(fc):>7} rows  published {fc.publishTime.min()} -> {fc.publishTime.max()}")
