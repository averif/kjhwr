import { useEffect, useState } from 'react'
import {
  fetchAccuracy, fetchGeneration, fetchHorizon, fetchMeta,
  type DailyError, type Filters, type GenerationPoint, type HorizonBucket, type Meta, type Summary,
} from './api'
import BarChartCard from './components/BarChartCard'
import Controls from './components/Controls'
import GenerationChart from './components/GenerationChart'
import StatCards from './components/StatCards'
import { formatDate, formatHour } from './format'

interface DashboardData {
  points: GenerationPoint[]
  summary: Summary
  daily: DailyError[]
  horizon: HorizonBucket[]
}

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null)
  const [filters, setFilters] = useState<Filters | null>(null)
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchMeta()
      .then((m) => {
        setMeta(m)
        setFilters({ start: m.firstDay, end: m.lastDay, decisionHour: m.defaultDecisionHour })
      })
      .catch((e: Error) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!filters) return
    let cancelled = false
    Promise.all([fetchGeneration(filters), fetchAccuracy(filters), fetchHorizon(filters)])
      .then(([generation, accuracy, horizon]) => {
        if (cancelled) return
        setData({ points: generation.points, ...accuracy, horizon: horizon.buckets })
        setError(null)
      })
      .catch((e: Error) => !cancelled && setError(e.message))
    return () => {
      cancelled = true
    }
  }, [filters])

  return (
    <main className="page">
      <header className="header">
        <div>
          <h1>WindLens</h1>
          <p className="subtitle">
            GB national wind generation: the day-ahead forecast you buy against, and how far to trust it.
          </p>
        </div>
        {meta && filters && <Controls meta={meta} filters={filters} onChange={setFilters} />}
      </header>

      {error && <div className="error" role="alert">Could not load data: {error}</div>}
      {!data && !error && <p className="muted">Loading…</p>}

      {data && filters && (
        <>
          <StatCards summary={data.summary} />

          <section className="card">
            <h2>Actual vs day-ahead forecast</h2>
            <p className="muted">
              For each hour, the latest forecast published before {formatHour(filters.decisionHour)} UTC the day
              before delivery — what was known when the purchase was made.
            </p>
            <GenerationChart points={data.points} />
          </section>

          <div className="grid-2">
            <section className="card">
              <h2>Daily forecast error</h2>
              <p className="muted">Mean absolute error of the day-ahead forecast per delivery day.</p>
              <BarChartCard
                bars={data.daily.map((d) => ({ label: formatDate(d.date), tooltip: formatDate(d.date), maeMw: d.maeMw }))}
              />
            </section>
            <section className="card">
              <h2>Error by forecast horizon</h2>
              <p className="muted">All published forecasts: how error grows with lead time.</p>
              <BarChartCard
                bars={data.horizon.map((b) => ({
                  label: `${b.horizonHours}h`,
                  tooltip: `${b.horizonHours}–${b.horizonHours + 6}h ahead (${b.count} forecasts)`,
                  maeMw: b.maeMw,
                }))}
              />
            </section>
          </div>
        </>
      )}

      <footer className="muted footer">
        Data: Elexon BMRS (FUELHH actual outturn, WINDFOR forecasts). Times in UTC.
      </footer>
    </main>
  )
}
