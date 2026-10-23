"""Load the pipeline output and select the forecasts a day-ahead trader would have seen."""

import json
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# GB day-ahead auctions close at 11:00 UK time on the day before delivery
# (UK time equals UTC in January), so that is the default decision time.
DEFAULT_DECISION_HOUR = 11


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class Forecast:
    published: datetime
    generation: float


@dataclass
class Dataset:
    actuals: dict[datetime, float]
    # Forecast versions per target time, sorted by publish time.
    forecasts: dict[datetime, list[Forecast]]

    @property
    def first_day(self) -> date:
        return min(self.actuals).date()

    @property
    def last_day(self) -> date:
        return max(self.actuals).date()


def load_dataset(data_dir: Path = DATA_DIR) -> Dataset:
    actual_rows = json.loads((data_dir / "actuals.json").read_text(encoding="utf-8"))
    forecast_rows = json.loads((data_dir / "forecasts.json").read_text(encoding="utf-8"))

    actuals = {parse_time(row["startTime"]): row["generation"] for row in actual_rows}
    forecasts: dict[datetime, list[Forecast]] = defaultdict(list)
    for row in forecast_rows:
        forecasts[parse_time(row["startTime"])].append(
            Forecast(parse_time(row["publishTime"]), row["generation"])
        )
    for versions in forecasts.values():
        versions.sort(key=lambda f: f.published)
    return Dataset(actuals, dict(forecasts))


@lru_cache
def get_dataset() -> Dataset:
    return load_dataset()


def decision_time(target: datetime, decision_hour: int) -> datetime:
    """When the day-ahead purchase for `target` must be made: D-1 at decision_hour."""
    day_before = target.date() - timedelta(days=1)
    return datetime.combine(day_before, time(decision_hour), timezone.utc)


def latest_before(versions: list[Forecast], cutoff: datetime) -> Forecast | None:
    """The most recently published forecast at or before `cutoff`."""
    index = bisect_right([f.published for f in versions], cutoff)
    return versions[index - 1] if index else None


def day_range(start: date, end: date) -> tuple[datetime, datetime]:
    """UTC [start 00:00, end+1 00:00) for an inclusive day range."""
    begin = datetime.combine(start, time(), timezone.utc)
    finish = datetime.combine(end + timedelta(days=1), time(), timezone.utc)
    return begin, finish


def generation_series(data: Dataset, start: date, end: date, decision_hour: int) -> list[dict]:
    """Half-hourly actuals alongside the day-ahead forecast available at decision time."""
    begin, finish = day_range(start, end)
    targets = sorted(t for t in set(data.actuals) | set(data.forecasts) if begin <= t < finish)

    points = []
    for target in targets:
        forecast = latest_before(data.forecasts.get(target, []), decision_time(target, decision_hour))
        points.append(
            {
                "time": target,
                "actual": data.actuals.get(target),
                "forecast": forecast.generation if forecast else None,
                "publishTime": forecast.published if forecast else None,
            }
        )
    return points


def forecast_versions(data: Dataset, start: date, end: date) -> list[tuple[float, float, float]]:
    """Every forecast version with an actual: (horizon hours, forecast, actual)."""
    begin, finish = day_range(start, end)
    rows = []
    for target, versions in data.forecasts.items():
        actual = data.actuals.get(target)
        if actual is None or not begin <= target < finish:
            continue
        for f in versions:
            rows.append(((target - f.published).total_seconds() / 3600, f.generation, actual))
    return rows
