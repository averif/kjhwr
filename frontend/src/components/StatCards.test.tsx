import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import StatCards from './StatCards'

const summary = {
  count: 744,
  maeMw: 1995.6,
  rmseMw: 2498.8,
  biasMw: 1728,
  nmaePct: 17.7,
  p90AbsErrorMw: 4183.9,
  maxAbsErrorMw: 6857,
}

describe('StatCards', () => {
  it('shows the headline accuracy metrics', () => {
    render(<StatCards summary={summary} />)

    expect(screen.getByText('1,996 MW')).toBeInTheDocument()
    expect(screen.getByText('17.7% of average wind output')).toBeInTheDocument()
    expect(screen.getByText('± 4,184 MW')).toBeInTheDocument()
    expect(screen.getByText('+1,728 MW')).toBeInTheDocument()
    expect(screen.getByText('Forecasts tend to overestimate')).toBeInTheDocument()
  })

  it('shows placeholders when there is no data', () => {
    render(
      <StatCards
        summary={{ count: 0, maeMw: null, rmseMw: null, biasMw: null, nmaePct: null, p90AbsErrorMw: null, maxAbsErrorMw: null }}
      />,
    )
    expect(screen.getAllByText('–').length).toBeGreaterThanOrEqual(3)
  })
})
