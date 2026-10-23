# API reference

Base URL: `http://localhost:8000` locally, or your Heroku URL in production. FastAPI also serves interactive docs at `/docs` and the OpenAPI schema at `/openapi.json`.

- **Authentication:** none. The API is read-only and serves public Elexon data.
- **Methods:** `GET` only.
- **CORS:** only the origins listed in the `ALLOWED_ORIGINS` environment variable (comma-separated), plus `localhost` on any port, can call it from a browser.
- **Times:** ISO 8601 in UTC. In January, UK local time equals UTC.
- **Units:** MW.

## Common query parameters

| Param | Type | Default | Description |
|---|---|---|---|
| `start` | `YYYY-MM-DD` | first day with data | First delivery day |
| `end` | `YYYY-MM-DD` | last day with data | Last delivery day (inclusive) |
| `decision_hour` | int 0–23 | `11` | Hour (UTC) on the day before delivery when the purchase is made |

If `start` is after `end`, or `decision_hour` is outside 0–23, the API returns `422`.

## `GET /api/health`

```json
{ "status": "ok" }
```

## `GET /api/meta`

The available data range and defaults.

```json
{ "firstDay": "2026-01-01", "lastDay": "2026-01-31", "defaultDecisionHour": 11 }
```

## `GET /api/generation?start&end&decision_hour`

Half-hourly actual generation, with the day-ahead forecast for each hour. For each target time, `forecast` is the most recently published forecast at or before `decision_hour`:00 on D-1. Forecasts are hourly, so `forecast` is `null` on :30 points.

```json
{
  "points": [
    { "time": "2026-01-01T00:00:00Z", "actual": 13756, "forecast": 19466, "publishTime": "2025-12-31T09:30:00Z" },
    { "time": "2026-01-01T00:30:00Z", "actual": 13873, "forecast": null, "publishTime": null }
  ]
}
```

## `GET /api/accuracy?start&end&decision_hour`

Accuracy of the day-ahead forecast. Error is defined as forecast minus actual, so a positive value means the forecast was too high.

```json
{
  "summary": {
    "count": 744,
    "maeMw": 2107.2,
    "rmseMw": 2611.2,
    "biasMw": 1839.9,
    "nmaePct": 18.2,
    "p90AbsErrorMw": 4377.0,
    "maxAbsErrorMw": 6857
  },
  "daily": [{ "date": "2026-01-01", "maeMw": 4273.9, "biasMw": 4273.9 }]
}
```

| Field | Meaning |
|---|---|
| `maeMw` | Mean absolute error |
| `rmseMw` | Root mean squared error (penalises large misses more) |
| `biasMw` | Mean error. Positive means the forecast was too high |
| `nmaePct` | MAE as a percentage of mean actual output. Used instead of MAPE, which breaks down when wind output is near zero |
| `p90AbsErrorMw` | 90% of hours had an absolute error at or below this value. Useful as a procurement buffer |
| `maxAbsErrorMw` | Largest absolute error in a single hour |

## `GET /api/accuracy/horizon?start&end`

MAE of **every** published forecast version, grouped into 6-hour bands by lead time (`startTime − publishTime`). This shows how forecast quality changes with lead time. `decision_hour` does not apply here.

```json
{ "buckets": [ { "horizonHours": 0, "maeMw": 1767.7, "count": 1488 }, { "horizonHours": 6, "maeMw": 1833.7, "count": 1488 } ] }
```
