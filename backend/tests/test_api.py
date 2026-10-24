import os


from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402

client = TestClient(app)


def test_meta():
    j = client.get("/api/meta").json()
    assert j["mode"] == "demo" and len(j["delivery_dates"]) == 31


def test_decision_day():
    j = client.get("/api/decision/2026-01-15").json()
    assert len(j["rows"]) == 48
    assert j["band"]["basis"] == "prior days"
    assert j["rows"][0]["lower"] <= j["rows"][0]["forecast"] <= j["rows"][0]["upper"]


def test_accuracy_and_horizon():
    a = client.get("/api/accuracy").json()
    assert a["overall"]["n"] == 31 * 48 and len(a["daily"]) == 31
    h = client.get("/api/horizon").json()
    assert h["decision_window_h"][0] < h["decision_window_h"][1]


def test_validation():
    assert client.get("/api/decision/2026-02-15").status_code == 404
    assert client.get("/api/decision/nope").status_code == 422
    assert client.get("/api/accuracy?cutoff=99").status_code == 422
