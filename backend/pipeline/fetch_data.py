"""Fetch UK national wind generation data from Elexon BMRS and store it as JSON.

Outputs (written to backend/data/):
  actuals.json    [{"startTime", "generation"}]                 half-hourly, from FUELHH
  forecasts.json  [{"startTime", "publishTime", "generation"}]  hourly, from WINDFOR

Run from the backend directory:
  python -m pipeline.fetch_data
"""

import json
import logging
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

API_BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Delivery days covered: January 2026.
DELIVERY_START = date(2026, 1, 1)
DELIVERY_END = date(2026, 1, 31)  # inclusive

# WINDFOR forecasts reach ~2.5 days ahead, so start publishing 3 days early
# to have every forecast horizon available for each delivery day.
FORECAST_LOOKBACK_DAYS = 3
MAX_FORECAST_HORIZON_HOURS = 72

log = logging.getLogger("pipeline")


def get_json(url: str, params: dict, retries: int = 3) -> list[dict]:
    """GET a BMRS stream endpoint, retrying transient failures with backoff."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ValueError(f"Expected a JSON list from {url}, got {type(data).__name__}")
            return data
        except (requests.RequestException, ValueError) as error:
            if attempt == retries:
                raise
            wait = 2**attempt
            log.warning("Request failed (%s), retrying in %ss (%d/%d)", error, wait, attempt, retries)
            time.sleep(wait)
    return []


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def in_delivery_window(start_time: str) -> bool:
    return DELIVERY_START <= parse_time(start_time).date() <= DELIVERY_END


def fetch_actuals() -> list[dict]:
    """Half-hourly outturn wind generation (FUELHH, fuelType=WIND)."""
    raw = get_json(
        f"{API_BASE}/FUELHH/stream",
        {
            # Widen by a day each side; we filter on UTC startTime below.
            "settlementDateFrom": (DELIVERY_START - timedelta(days=1)).isoformat(),
            "settlementDateTo": (DELIVERY_END + timedelta(days=1)).isoformat(),
            "fuelType": "WIND",
        },
    )
    log.info("FUELHH: received %d raw records", len(raw))

    # If a period was republished, keep the most recent value.
    latest: dict[str, dict] = {}
    for record in raw:
        start, value = record.get("startTime"), record.get("generation")
        if record.get("fuelType") != "WIND" or not start or value is None:
            continue
        if not in_delivery_window(start):
            continue
        current = latest.get(start)
        if current is None or record.get("publishTime", "") > current["publishTime"]:
            latest[start] = {"publishTime": record.get("publishTime", ""), "generation": value}

    return [
        {"startTime": start, "generation": latest[start]["generation"]}
        for start in sorted(latest)
    ]


def fetch_forecasts() -> list[dict]:
    """Hourly wind generation forecasts (WINDFOR), every published version."""
    publish_from = datetime.combine(
        DELIVERY_START - timedelta(days=FORECAST_LOOKBACK_DAYS), datetime.min.time(), timezone.utc
    )
    publish_to = datetime.combine(DELIVERY_END + timedelta(days=1), datetime.min.time(), timezone.utc)
    raw = get_json(
        f"{API_BASE}/WINDFOR/stream",
        {
            "publishDateTimeFrom": publish_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publishDateTimeTo": publish_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )
    log.info("WINDFOR: received %d raw records", len(raw))

    unique: dict[tuple[str, str], int] = {}
    for record in raw:
        start, published, value = record.get("startTime"), record.get("publishTime"), record.get("generation")
        if not start or not published or value is None or not in_delivery_window(start):
            continue
        # Keep forward-looking forecasts only (WINDFOR also restates recent past hours).
        horizon = (parse_time(start) - parse_time(published)).total_seconds() / 3600
        if 0 <= horizon <= MAX_FORECAST_HORIZON_HOURS:
            unique[(start, published)] = value

    return [
        {"startTime": start, "publishTime": published, "generation": value}
        for (start, published), value in sorted(unique.items())
    ]


def save(name: str, records: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / name
    path.write_text(json.dumps(records, separators=(",", ":")), encoding="utf-8")
    log.info("Saved %d records to %s", len(records), path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log.info("Delivery window: %s to %s", DELIVERY_START, DELIVERY_END)

    actuals = fetch_actuals()
    forecasts = fetch_forecasts()
    if not actuals or not forecasts:
        raise SystemExit("No data returned from Elexon; nothing saved.")

    expected = ((DELIVERY_END - DELIVERY_START).days + 1) * 48
    if len(actuals) < expected:
        log.warning("Actuals incomplete: %d of %d half-hours", len(actuals), expected)

    save("actuals.json", actuals)
    save("forecasts.json", forecasts)


if __name__ == "__main__":
    main()
