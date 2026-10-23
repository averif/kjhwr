"""Forecast accuracy metrics. Errors are forecast minus actual, in MW."""

import math
from collections import defaultdict
from statistics import mean


def percentile(values: list[float], pct: float) -> float:
    """Linear-interpolated percentile of a non-empty list."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * pct / 100
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def summarise(pairs: list[tuple[float, float]]) -> dict:
    """Accuracy summary for (forecast, actual) pairs."""
    if not pairs:
        return {"count": 0, "maeMw": None, "rmseMw": None, "biasMw": None,
                "nmaePct": None, "p90AbsErrorMw": None, "maxAbsErrorMw": None}

    errors = [f - a for f, a in pairs]
    abs_errors = [abs(e) for e in errors]
    mae = mean(abs_errors)
    mean_actual = mean(a for _, a in pairs)
    return {
        "count": len(pairs),
        "maeMw": round(mae, 1),
        "rmseMw": round(math.sqrt(mean(e * e for e in errors)), 1),
        "biasMw": round(mean(errors), 1),
        # MAE relative to mean generation; MAPE is unstable when wind output is near zero.
        "nmaePct": round(100 * mae / mean_actual, 1) if mean_actual else None,
        "p90AbsErrorMw": round(percentile(abs_errors, 90), 1),
        "maxAbsErrorMw": round(max(abs_errors), 1),
    }


def daily_errors(points: list[dict]) -> list[dict]:
    """MAE and bias per delivery day from generation-series points."""
    by_day: dict[str, list[float]] = defaultdict(list)
    for p in points:
        if p["actual"] is not None and p["forecast"] is not None:
            by_day[p["time"].date().isoformat()].append(p["forecast"] - p["actual"])
    return [
        {"date": day, "maeMw": round(mean(abs(e) for e in errs), 1), "biasMw": round(mean(errs), 1)}
        for day, errs in sorted(by_day.items())
    ]


def errors_by_horizon(rows: list[tuple[float, float, float]], bucket_hours: int = 6) -> list[dict]:
    """MAE grouped by how far ahead the forecast was published."""
    buckets: dict[int, list[float]] = defaultdict(list)
    for horizon, forecast, actual in rows:
        buckets[int(horizon // bucket_hours) * bucket_hours].append(abs(forecast - actual))
    return [
        {"horizonHours": h, "maeMw": round(mean(errs), 1), "count": len(errs)}
        for h, errs in sorted(buckets.items())
    ]
