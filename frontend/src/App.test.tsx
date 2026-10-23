import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { buildQuery } from './api'

const responses: Record<string, unknown> = {
  '/api/meta': { firstDay: '2026-01-02', lastDay: '2026-01-03', defaultDecisionHour: 11 },
  '/api/generation': {
    points: [{ time: '2026-01-02T00:00:00Z', actual: 1000, forecast: 1100, publishTime: '2026-01-01T09:30:00Z' }],
  },
  '/api/accuracy': {
    summary: { count: 1, maeMw: 100, rmseMw: 100, biasMw: 100, nmaePct: 10, p90AbsErrorMw: 100, maxAbsErrorMw: 100 },
    daily: [{ date: '2026-01-02', maeMw: 100, biasMw: 100 }],
  },
  '/api/accuracy/horizon': { buckets: [{ horizonHours: 0, maeMw: 100, count: 1 }] },
}

function mockFetch(ok = true) {
  return vi.fn(async (url: string) => {
    const path = new URL(url).pathname
    return { ok, status: ok ? 200 : 500, json: async () => responses[path] } as Response
  })
}

afterEach(() => vi.unstubAllGlobals())

describe('App', () => {
  it('loads data and renders the dashboard', async () => {
    const fetchMock = mockFetch()
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    expect(await screen.findByText('Actual vs day-ahead forecast')).toBeInTheDocument()
    expect(screen.getByText('Mean absolute error')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/generation?start=2026-01-02&end=2026-01-03&decision_hour=11'))
  })

  it('shows an error when the API is unavailable', async () => {
    vi.stubGlobal('fetch', mockFetch(false))
    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load data')
  })
})

describe('buildQuery', () => {
  it('omits the decision hour when asked', () => {
    expect(buildQuery({ start: '2026-01-02', end: '2026-01-05', decisionHour: 11 }, false)).toBe(
      'start=2026-01-02&end=2026-01-05',
    )
  })
})
