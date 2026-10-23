# Data pipeline

`backend/pipeline/fetch_data.py` downloads national wind data from the Elexon BMRS API, cleans it, and writes two compact JSON files that the API serves.

## Run

```bash
cd backend
pip install -r requirements.txt   # needs only `requests`
python -m pipeline.fetch_data
```

The script logs progress to stdout. A full run takes about 5 seconds.

## Sources

| Dataset | Endpoint | Used fields |
|---|---|---|
| Actual generation | [`FUELHH/stream`](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream), `fuelType=WIND` | `startTime`, `generation` (MW, half-hourly) |
| Forecasts | [`WINDFOR/stream`](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream) | `startTime`, `publishTime`, `generation` (MW, hourly) |

## Time window

The app covers **delivery days 1 to 31 January 2026**. The window is set by `DELIVERY_START` and `DELIVERY_END` at the top of the script. The script fetches:

- **Actuals:** settlement dates one day either side of that window, then filters on UTC `startTime`.
- **Forecasts:** published from 29 Dec 2025 to 1 Feb 2026. `WINDFOR` looks up to about 2.5 days ahead, so starting 3 days early gives every lead time for every delivery day. Without this, the forecast-horizon analysis would be incomplete.

## Processing

- Drops records with no `startTime`, `publishTime` or `generation`.
- **Actuals:** if Elexon republished a half-hour, only the value with the latest `publishTime` is kept.
- **Forecasts:** every published version is kept, because the API needs them to choose which forecast was available at decision time. Forecasts with a negative horizon (`WINDFOR` also restates recent past hours) or a horizon over 72 h are dropped. Exact duplicates are removed.
- Output is sorted, minified JSON:
  - `data/actuals.json`: `[{"startTime", "generation"}]` (1,488 rows = 31 days × 48)
  - `data/forecasts.json`: `[{"startTime", "publishTime", "generation"}]` (~14k rows)

## Error handling

- Each request uses a 60 s timeout and 3 attempts with exponential backoff (2 s, 4 s). Non-2xx responses and non-list payloads count as failures.
- If either dataset comes back empty, the script exits with an error and **does not overwrite** the existing files.
- It logs a warning if the actuals don't cover every half-hour in the window.

## Why JSON files rather than a database

The dataset is about 1.4 MB and never changes after it is fetched. Committing it next to the API keeps deployment to one stateless container, with no database to provision and no network calls at request time. If the app later covers more months or refreshes live, the next step would be SQLite or Postgres, with the pipeline run on a schedule.
