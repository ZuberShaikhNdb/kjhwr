"""Central configuration. Everything can be overridden with environment variables."""
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Scope of the assignment: purchase decisions made in January 2026.
# A "delivery date" is the day the power is delivered; the purchase decision is made the day before.
DELIVERY_START = date.fromisoformat(os.getenv("DELIVERY_START", "2026-01-01"))
DELIVERY_END = date.fromisoformat(os.getenv("DELIVERY_END", "2026-01-31"))

TIMEZONE = "Europe/London"

# Time (UK local) on the day before delivery by which the day-ahead decision must be made.
# GB day-ahead auctions close mid-morning; 09:30 is a configurable, documented assumption.
DEFAULT_CUTOFF = os.getenv("DECISION_CUTOFF", "09:30")
CUTOFF_OPTIONS = ["08:00", "09:00", "09:30", "10:00", "11:00"]

ELEXON_BASE = os.getenv("ELEXON_BASE", "https://data.elexon.co.uk/bmrs/api/v1")

SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", ROOT / "data" / "snapshot"))
STATIC_DIR = Path(os.getenv("STATIC_DIR", ROOT / "frontend" / "dist"))

# DEMO_MODE=1 uses clearly-labelled synthetic data (for offline development / tests only).
DEMO_MODE = os.getenv("DEMO_MODE", "0") == "1"
