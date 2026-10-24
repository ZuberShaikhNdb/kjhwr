# Video script (≤10 min total)

## Part 1: Customer pitch (≈4:30)
1. **Problem (0:30)** You buy day-ahead; wind is weather-driven; you decide the day before, so you rely on a forecast.
2. **Tomorrow's wind tab (1:30)** Pick a January day. "This is the newest forecast available at your 09:30 deadline, with its publish time." Point to the shaded band: "90% of past errors fall here, so you can see how much to hedge." Toggle *Show what actually happened*.
3. **Forecast accuracy tab (1:30)** Headline numbers: MAE, P90, bias. Daily bars: "Some days are far harder." Time-of-day chart: where to hold more buffer. Histogram: tails.
4. **Lead time tab (0:45)** Error grows with lead time; the shaded zone is what your decisions actually use. Changing the deadline moves the numbers.
5. **Close (0:15)** Same data you already trust (Elexon); extendable to demand/solar/prices.

## Part 2: Tech-lead review (≈4:30)
1. **Architecture (1:00)** React → FastAPI → pandas; CSV snapshot of Elexon data; one Docker image serves API + UI; Vercel/Heroku configs.
2. **Core logic (1:30)** Open `analysis.py`: `cutoff_utc` (D-1 at local time, DST-safe) → `decision_forecasts` (latest publishTime ≤ cutoff) → `build_eval` → `metrics`. Sign convention. `error_band` has no look-ahead.
3. **Data layer (0:45)** `elexon.py` chunking/retry; `data.py` fallback order snapshot → live → demo-only-by-flag.
4. **API + frontend (0:45)** Four endpoints; `useApi` hook; one component per tab; mobile-first CSS.
5. **Quality (0:30)** `pytest` (9 tests: cutoff, selection, metrics, no-look-ahead, API validation). Next steps: add demand/solar, caching, CI.
