from datetime import datetime, timezone

import pytest

from app.metrics import daily_errors, errors_by_horizon, percentile, summarise


def test_summarise_basic_metrics():
    # errors: +100, -100, +300
    result = summarise([(1100, 1000), (900, 1000), (1300, 1000)])

    assert result["count"] == 3
    assert result["maeMw"] == pytest.approx(166.7)
    assert result["biasMw"] == pytest.approx(100.0)
    assert result["rmseMw"] == pytest.approx(191.5)
    assert result["nmaePct"] == pytest.approx(16.7)
    assert result["maxAbsErrorMw"] == 300


def test_summarise_empty_returns_nulls():
    result = summarise([])
    assert result["count"] == 0
    assert result["maeMw"] is None


def test_percentile_interpolates():
    assert percentile([0, 10], 50) == 5
    assert percentile([1, 2, 3, 4, 5], 90) == pytest.approx(4.6)


def test_daily_errors_skips_missing_values():
    day = lambda h: datetime(2026, 1, 2, h, tzinfo=timezone.utc)
    points = [
        {"time": day(0), "actual": 100, "forecast": 150},
        {"time": day(1), "actual": 100, "forecast": None},
        {"time": day(2), "actual": 100, "forecast": 50},
    ]
    assert daily_errors(points) == [{"date": "2026-01-02", "maeMw": 50.0, "biasMw": 0.0}]


def test_errors_by_horizon_buckets():
    rows = [(1.0, 110, 100), (5.5, 130, 100), (7.0, 100, 100)]
    assert errors_by_horizon(rows, bucket_hours=6) == [
        {"horizonHours": 0, "maeMw": 20.0, "count": 2},
        {"horizonHours": 6, "maeMw": 0.0, "count": 1},
    ]
