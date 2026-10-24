import pandas as pd
import pytest

from backend.app import analysis
from backend.app.demo import make_demo


def _fc(rows):
    return pd.DataFrame(rows, columns=["publishTime", "startTime", "generation"]).assign(
        publishTime=lambda d: pd.to_datetime(d.publishTime, utc=True), startTime=lambda d: pd.to_datetime(d.startTime, utc=True))


def test_cutoff_is_day_before_local_time():
    s = pd.Series(pd.to_datetime(["2026-01-10 00:00", "2026-01-10 23:30"], utc=True))
    out = analysis.cutoff_utc(s, "09:30")
    assert all(out == pd.Timestamp("2026-01-09 09:30", tz="UTC"))  # January = GMT, so local == UTC


def test_decision_forecast_picks_latest_before_cutoff():
    fc = _fc([
        ("2026-01-09 06:00", "2026-01-10 12:00", 100.0),
        ("2026-01-09 09:00", "2026-01-10 12:00", 200.0),   # latest allowed (09:00 <= 09:30)
        ("2026-01-09 10:00", "2026-01-10 12:00", 300.0),   # published after cutoff -> unusable
    ])
    d = analysis.decision_forecasts(fc, "09:30")
    assert len(d) == 1 and d.iloc[0]["forecast"] == 200.0
    assert d.iloc[0]["horizon_h"] == pytest.approx(27.0)


def test_metrics_and_sign_convention():
    ev = pd.DataFrame({"forecast": [110.0, 90.0], "actual": [100.0, 100.0]})
    ev["error"] = ev.forecast - ev.actual
    m = analysis.metrics(ev)
    assert m["mae"] == 10.0 and m["bias"] == 0.0 and m["rmse"] == 10.0 and m["over_forecast_pct"] == 50.0
    assert m["wape_pct"] == 10.0


def test_error_band_has_no_lookahead():
    act, fc = make_demo()
    ev = analysis.build_eval(fc, act, "09:30")
    ev = ev[ev.delivery_date >= "2026-01-01"]
    b = analysis.error_band(ev, "2026-01-10")
    assert b["basis"] == "prior days" and b["days"] == 9


def test_end_to_end_demo_pipeline():
    act, fc = make_demo()
    ev = analysis.build_eval(fc, act, "09:30")
    assert ev["horizon_h"].between(14, 40).all()
    hz = analysis.horizon_metrics(fc, act, "2026-01-01", "2026-01-31")
    maes = [b["mae"] for b in hz]
    assert maes[-1] > maes[0]  # error grows with lead time in the synthetic data
