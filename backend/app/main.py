import os
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .data import DEFAULT_DECISION_HOUR, forecast_versions, generation_series, get_dataset
from .metrics import daily_errors, errors_by_horizon, summarise

app = FastAPI(title="WindLens API", version="1.0.0")

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o],
    # Local dev servers on any port (Vite moves to 5174+ when 5173 is busy).
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["GET"],
    allow_headers=["*"],
)


def resolve_range(start: date | None, end: date | None) -> tuple[date, date]:
    data = get_dataset()
    start, end = start or data.first_day, end or data.last_day
    if start > end:
        raise HTTPException(status_code=422, detail="start must be on or before end")
    return start, end


StartQuery = Query(None, description="First delivery day (YYYY-MM-DD); defaults to the first day with data")
EndQuery = Query(None, description="Last delivery day, inclusive; defaults to the last day with data")
DecisionHourQuery = Query(
    DEFAULT_DECISION_HOUR, ge=0, le=23, description="Hour (UTC) on D-1 when the day-ahead purchase is made"
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/meta")
def meta() -> dict:
    data = get_dataset()
    return {
        "firstDay": data.first_day,
        "lastDay": data.last_day,
        "defaultDecisionHour": DEFAULT_DECISION_HOUR,
    }


@app.get("/api/generation")
def generation(start: date | None = StartQuery, end: date | None = EndQuery,
               decision_hour: int = DecisionHourQuery) -> dict:
    start, end = resolve_range(start, end)
    return {"points": generation_series(get_dataset(), start, end, decision_hour)}


@app.get("/api/accuracy")
def accuracy(start: date | None = StartQuery, end: date | None = EndQuery,
             decision_hour: int = DecisionHourQuery) -> dict:
    start, end = resolve_range(start, end)
    points = generation_series(get_dataset(), start, end, decision_hour)
    pairs = [(p["forecast"], p["actual"]) for p in points
             if p["forecast"] is not None and p["actual"] is not None]
    return {"summary": summarise(pairs), "daily": daily_errors(points)}


@app.get("/api/accuracy/horizon")
def accuracy_by_horizon(start: date | None = StartQuery, end: date | None = EndQuery) -> dict:
    start, end = resolve_range(start, end)
    return {"buckets": errors_by_horizon(forecast_versions(get_dataset(), start, end))}
