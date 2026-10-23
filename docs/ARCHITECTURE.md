# Architecture and design notes

```
Elexon BMRS API ──► pipeline/fetch_data.py ──► data/*.json ──► FastAPI (Heroku, Docker) ──► React + Recharts (Vercel)
   FUELHH, WINDFOR        fetch, clean, dedupe        committed     in-memory, pure functions        dashboard
```

## Main design decisions

**Defining "the forecast available at decision time".** The brief asks for the latest forecast available when the day-ahead purchase is made. GB day-ahead auctions close at 11:00 UK time on D-1, so for each target hour the app uses the most recent `WINDFOR` forecast published at or before D-1 11:00 (in practice the 09:30 run). The decision hour is a parameter, so a team with an earlier internal cut-off can see how its accuracy changes. All of this logic is in `app/data.py`: `decision_time` and `latest_before` (a binary search over publish times).

**Comparing at the forecast's resolution.** `WINDFOR` is hourly and `FUELHH` is half-hourly. Accuracy is measured only on the hourly target times, where both datasets have a value. Interpolating the forecast would invent data. The chart still plots every half-hour of actual generation.

**Choosing metrics a buyer can act on.** MAE gives the typical miss in MW. The P90 absolute error is a buffer that would have covered 90% of hours. Bias shows systematic over- or under-forecasting, which is the main finding for this month. I used nMAE rather than MAPE because wind output can be close to zero, which makes MAPE unstable.

**Keeping the backend simple.** The backend has no database, no pandas and no ORM. It loads about 15k rows into dictionaries once at startup (`lru_cache`), and every endpoint is a thin wrapper around pure functions in `data.py` and `metrics.py`. That keeps the logic easy to unit-test without HTTP. The API tests swap in a small fixture dataset with `monkeypatch`, so the expected values can be worked out by hand.

**Frontend.** The frontend uses React with TypeScript on Vite, Recharts for the charts and plain CSS custom properties for light and dark themes. Create React App, which the original plan named, is deprecated and no longer maintained, so I used Vite, its usual replacement. The layout is one page: controls, four headline stat cards, the main actual-vs-forecast chart, then two diagnostic charts. Breakpoints go from 4 to 2 columns. Chart colours come from a colour-blind-safe palette, and every chart has a hover tooltip.

## Challenges and how I handled them

- **Forecast versions.** Each target hour has up to ~20 forecast versions, published about 8 times a day, plus restatements of past hours. I kept every forward-looking version in the pipeline and chose between them at query time. That one dataset supports both the decision-time view and the horizon analysis.
- **Data window.** The app covers delivery days in January 2026. Forecasts have to be fetched from late December so that the first days of January have long-lead forecasts. The day-ahead forecast for 1 January, for example, was published on 31 December.
- **Large systematic bias.** A bias of +1.8 GW looked like a bug at first. I checked it against the raw API values, and it is real. The likely explanation is curtailment, as noted in the README. I made it a headline metric with a plain-language note rather than hiding it.

## Possible next steps

- Use the forecast error distribution to recommend a purchase volume, for example the forecast minus the P90 error.
- Break error down by hour of day and by wind level, since error is larger at high output.
- Run the pipeline on a schedule, move to Postgres, and widen the date range.

## Demo video outline (max 10 min)

**Part 1: client pitch (≤5 min)**

1. The problem: you buy the day before, and wind is uncertain.
2. Walk through the dashboard: the decision-time forecast, and the actual-vs-forecast chart.
3. Headline result: a typical miss of ~2.1 GW, and a buffer of ±4.4 GW that covers 90% of hours.
4. Key insight: the forecast runs high, so buying against it leaves you short.
5. Change the decision hour and date range: error grows with lead time.

**Part 2: tech lead review (≤5 min)**

1. Architecture diagram (above), and the repository layout.
2. The pipeline: windowing, dedupe, retries, why JSON.
3. `data.py`: the decision-time selection logic. `metrics.py`: pure functions.
4. Tests (pytest with fixtures, Vitest with mocked fetch), then the CI/CD workflow.
5. Docker, Heroku and Vercel deployment, security headers and CORS.
