import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.data import load_dataset

ACTUALS = [
    {"startTime": "2026-01-02T00:00:00Z", "generation": 1000},
    {"startTime": "2026-01-02T00:30:00Z", "generation": 1100},
    {"startTime": "2026-01-02T01:00:00Z", "generation": 1200},
    {"startTime": "2026-01-03T00:00:00Z", "generation": 2000},
]

FORECASTS = [
    # Target 2026-01-02 00:00 — decision time (11:00 default) is 2026-01-01 11:00.
    {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2025-12-31T09:30:00Z", "generation": 500},
    {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-01T09:30:00Z", "generation": 900},
    {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-01T15:30:00Z", "generation": 1000},
    {"startTime": "2026-01-02T01:00:00Z", "publishTime": "2026-01-01T09:30:00Z", "generation": 1500},
    {"startTime": "2026-01-03T00:00:00Z", "publishTime": "2026-01-02T09:30:00Z", "generation": 2100},
]


@pytest.fixture
def client(tmp_path, monkeypatch):
    (tmp_path / "actuals.json").write_text(json.dumps(ACTUALS))
    (tmp_path / "forecasts.json").write_text(json.dumps(FORECASTS))
    dataset = load_dataset(tmp_path)
    monkeypatch.setattr(main, "get_dataset", lambda: dataset)
    return TestClient(main.app)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_meta_reports_data_range(client):
    body = client.get("/api/meta").json()
    assert body == {"firstDay": "2026-01-02", "lastDay": "2026-01-03", "defaultDecisionHour": 11}


def test_generation_uses_latest_forecast_before_decision_time(client):
    points = client.get("/api/generation", params={"start": "2026-01-02", "end": "2026-01-02"}).json()["points"]

    assert [p["time"] for p in points] == [
        "2026-01-02T00:00:00Z", "2026-01-02T00:30:00Z", "2026-01-02T01:00:00Z",
    ]
    first = points[0]
    assert first["actual"] == 1000
    assert first["forecast"] == 900  # 15:30 version was published after the 11:00 decision
    assert first["publishTime"] == "2026-01-01T09:30:00Z"
    assert points[1]["forecast"] is None  # forecasts are hourly


def test_generation_respects_decision_hour(client):
    points = client.get(
        "/api/generation", params={"start": "2026-01-02", "end": "2026-01-02", "decision_hour": 16}
    ).json()["points"]
    assert points[0]["forecast"] == 1000

    early = client.get(
        "/api/generation", params={"start": "2026-01-02", "end": "2026-01-02", "decision_hour": 8}
    ).json()["points"]
    assert early[0]["forecast"] == 500  # D-1 09:30 not yet published, fall back to D-2


def test_accuracy_summary_and_daily(client):
    body = client.get("/api/accuracy").json()

    # errors: -100 (Jan 2 00:00), +300 (Jan 2 01:00), +100 (Jan 3 00:00)
    assert body["summary"]["count"] == 3
    assert body["summary"]["maeMw"] == pytest.approx(166.7)
    assert body["summary"]["biasMw"] == pytest.approx(100.0)
    assert body["daily"] == [
        {"date": "2026-01-02", "maeMw": 200.0, "biasMw": 100.0},
        {"date": "2026-01-03", "maeMw": 100.0, "biasMw": 100.0},
    ]


def test_accuracy_by_horizon(client):
    buckets = client.get("/api/accuracy/horizon").json()["buckets"]
    assert sum(b["count"] for b in buckets) == len(FORECASTS)
    assert [b["horizonHours"] for b in buckets] == sorted(b["horizonHours"] for b in buckets)


def test_rejects_inverted_range(client):
    response = client.get("/api/accuracy", params={"start": "2026-01-03", "end": "2026-01-02"})
    assert response.status_code == 422


def test_rejects_invalid_decision_hour(client):
    assert client.get("/api/generation", params={"decision_hour": 24}).status_code == 422
