# WindLens

A web app for a UK energy utility's day-ahead trading team. It answers two questions:

1. **What was the latest wind forecast available when we had to buy?** For every hour of a delivery day, it shows the most recent national wind forecast published before the day-ahead decision time (default 11:00 UTC on D-1, when the GB day-ahead auctions close).
2. **How much can we trust it?** It measures that forecast against actual generation: mean absolute error, the 90th-percentile error to use as a procurement buffer, bias, the worst hour, and how error grows with forecast lead time.

Scope follows the brief: national wind only, from Elexon BMRS, for delivery days **1 to 31 January 2026**.

- **Live app:** _<add Vercel URL>_
- **API:** _<add Heroku URL>_/docs

## Key findings (January 2026, 11:00 decision time)

| Metric | Value |
|---|---|
| Mean absolute error | 2,107 MW (18.2% of average wind output) |
| 90% of hours within | ± 4,377 MW |
| Average bias | +1,840 MW: the forecast is usually higher than actual output |
| Worst hour | 6,857 MW |
| Error by lead time | ~1.8 GW at 0–6 h ahead, rising to ~2.4 GW at 42 h+ |

The large positive bias is the most useful finding for a buyer: relying on the raw forecast tends to leave them **short**. One likely cause is that `FUELHH` records metered output after curtailment, while `WINDFOR` forecasts what the wind fleet could produce. This needs checking with more data.

## Repository layout

```
backend/
  pipeline/fetch_data.py   Downloads FUELHH + WINDFOR from Elexon, cleans them, writes data/*.json
  data/                    Processed data (committed, so the API needs no network access)
  app/data.py              Loads data; picks the latest forecast before the decision time
  app/metrics.py           Accuracy metrics (MAE, RMSE, bias, P90, by day, by horizon)
  app/main.py              FastAPI app and endpoints
  tests/                   pytest unit + API tests
  Dockerfile
frontend/
  src/App.tsx              Page layout, data loading and state
  src/api.ts               Typed API client
  src/components/          Controls, StatCards, GenerationChart, BarChartCard
  src/*.test.tsx           Vitest + Testing Library tests
  Dockerfile, nginx.conf   Production container (static build served by nginx)
  vercel.json              Security headers for the Vercel deployment
docs/
  PIPELINE.md              How the data pipeline works and how to run it
  API.md                   Endpoint reference
  ARCHITECTURE.md          Design decisions, challenges, demo video outline
.github/workflows/ci-cd.yml  Test, build, and deploy on push to main
docker-compose.yml         Run the whole stack locally
heroku.yml                 Heroku container build config
```

## Run locally

Requirements: Python 3.12+ and Node 22+ (or just Docker).

**Backend** (http://localhost:8000, interactive docs at `/docs`):

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

**Frontend** (http://localhost:5173):

```bash
cd frontend
npm install
npm run dev
```

The frontend calls `http://localhost:8000` by default. To use a different API, set `VITE_API_URL`.

**With Docker** (frontend on http://localhost:3000, API on http://localhost:8000):

```bash
docker compose up --build
```

**Refresh the data** (optional, because the processed data is already committed):

```bash
cd backend
python -m pipeline.fetch_data
```

**Tests:**

```bash
cd backend && pytest
cd frontend && npm test
```

## Deployment

The pipeline in `.github/workflows/ci-cd.yml` runs on every push and pull request. It runs the backend tests, the frontend lint, tests and build, and builds both Docker images. On a push to `main` it also deploys both apps.

### Backend on Heroku (container stack)

1. Create the app: `heroku create <app-name> --stack container`.
2. Set allowed origins: `heroku config:set ALLOWED_ORIGINS=https://<your-vercel-domain> --app <app-name>`.
3. Add GitHub repository secrets `HEROKU_API_KEY` and `HEROKU_APP_NAME`.

To deploy by hand: `heroku container:push web --context-path backend` then `heroku container:release web`.

### Frontend on Vercel

1. In `frontend/`, run `vercel link` to create the project. Vercel detects Vite automatically.
2. In the Vercel project settings, set the environment variable `VITE_API_URL=https://<app-name>.herokuapp.com`.
3. Add GitHub secrets `VERCEL_TOKEN`, `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID`. The two IDs are in `frontend/.vercel/project.json` after you link.

### Security and performance

- The API is read-only (`GET` only) and has no user data. CORS is limited to `ALLOWED_ORIGINS` plus `localhost` on any port, for local development.
- Containers run as a non-root user. The frontend sends `nosniff`, `X-Frame-Options` and referrer-policy headers.
- Data is loaded into memory once at startup. Each request is a few milliseconds of pure Python with no database or external calls. Responses are gzip-compressed, and uvicorn runs 2 workers.

## Use of AI tools

I explored the Elexon data and wrote the initial fetch scripts myself, which is where I found the forecast-versioning and resolution issues. I then used **Claude Code** (Anthropic) to speed up the implementation, and directed and reviewed the design: how to pick the decision-time forecast, which metrics matter to a buyer, and the scope.
