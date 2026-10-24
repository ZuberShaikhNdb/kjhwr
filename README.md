# Wind Forecast Monitor

Web app for a GB energy utility's day-ahead desk. It answers two questions using only Elexon BMRS data
(national wind, **FUELHH** actuals and **WINDFOR** forecasts) for purchase decisions made in **January 2026**:

1. **What is the latest wind forecast I can rely on when I must buy?** → *Tomorrow's wind* tab
2. **How wrong is that forecast, quantitatively?** → *Forecast accuracy* and *Accuracy vs lead time* tabs

**Stack:** React (Vite + Recharts) · Python **FastAPI** + pandas · Docker · Vercel / Heroku.

> **AI disclosure:** this project was built with the assistance of Claude (Anthropic) for code generation and design.
> All logic was reviewed and covered by unit tests.

**Live app:** `<PASTE VERCEL/HEROKU URL HERE>`

## Key idea: the "decision forecast"
For delivery date **D**, power is bought on **D-1** before a deadline (default **09:30 UK time**, selectable in the UI).
For every half-hour of D we take the **most recent WINDFOR forecast with `publishTime` ≤ deadline**. That is exactly what
the buyer could have seen. We then compare it with FUELHH actuals. `error = forecast − actual` (positive = forecast too high,
i.e. risk of under-buying).

Metrics: MAE, RMSE, bias, WAPE (error as % of generation), P50/P90/P95 absolute error, max error, % of slots over-forecast.
The shaded **90% band** on the main chart uses the 5th–95th percentile of past errors from *earlier days only* (no look-ahead).

## Repo layout
```
backend/app/main.py       FastAPI routes (/api/meta, /decision/{date}, /accuracy, /horizon) + serves built UI
backend/app/analysis.py   Pure analysis functions (decision forecast, metrics, error band, horizon analysis)
backend/app/elexon.py     Elexon API client (FUELHH, WINDFOR; chunked + retried)
backend/app/data.py       Loads CSV snapshot -> falls back to live fetch
backend/app/demo.py       Synthetic data (DEMO_MODE=1 only; used by tests)
backend/app/config.py     Settings (dates, cutoff, paths) via env vars
backend/tests/            pytest unit + API tests
frontend/src/             React app (App, DecisionTab, AccuracyTab, HorizonTab, shared UI)
scripts/fetch_data.py     One-off download of Elexon data into data/snapshot/
data/snapshot/            actuals.csv + forecasts.csv (created by the script, committed for fast deploys)
api/index.py              Vercel serverless entrypoint
Dockerfile, docker-compose.yml, heroku.yml, vercel.json   packaging / deployment
VIDEO_SCRIPT.md           Talking points for the two-part demo video
```

## Start the application
**Step 0 – download the data once (needs internet, ~1–2 min):**
```bash
pip install -r requirements.txt
python scripts/fetch_data.py        # writes data/snapshot/actuals.csv and forecasts.csv
```
(If you skip this, the backend fetches live from Elexon on first request, which is slower.)

**Docker (recommended):**
```bash
docker compose up --build           # → http://localhost:8000
```
**Local dev:**
```bash
make backend                        # API on :8000   (or: uvicorn backend.app.main:app --reload)
make frontend                       # UI on :5173, proxies /api
```
**Tests:** `pip install -r requirements-dev.txt && python -m pytest -q`

## Deploy
**Vercel** (static React + Python serverless function): import the repo, keep defaults (`vercel.json` does the rest).
Make sure `data/snapshot/*.csv` is committed so the function does not need to call Elexon.

**Heroku** (container):
```bash
heroku create && heroku stack:set container
git push heroku main
```

## Assumptions & limitations
- Decision deadline is an assumption (09:30 UK on D-1); change it in the UI or with `DECISION_CUTOFF`.
- Scope is national wind only; no demand, solar or price data, so the app shows wind supply and its uncertainty, not the MW to procure.
- If a slot has several FUELHH rows, the latest published one is kept.
- Forecast error is not independent between half-hours (weather is persistent); the band is per-slot, not a portfolio-level interval.
