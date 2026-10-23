import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import Controls from './Controls'

const meta = { firstDay: '2026-01-02', lastDay: '2026-02-01', defaultDecisionHour: 11 }
const filters = { start: '2026-01-02', end: '2026-02-01', decisionHour: 11 }

describe('Controls', () => {
  it('reports a new decision hour', () => {
    const onChange = vi.fn()
    render(<Controls meta={meta} filters={filters} onChange={onChange} />)

    fireEvent.change(screen.getByLabelText(/decision time/i), { target: { value: '9' } })

    expect(onChange).toHaveBeenCalledWith({ ...filters, decisionHour: 9 })
  })

  it('reports a new start date and limits it to the data range', () => {
    const onChange = vi.fn()
    render(<Controls meta={meta} filters={filters} onChange={onChange} />)
    const from = screen.getByLabelText('From')

    expect(from).toHaveAttribute('min', '2026-01-02')
    fireEvent.change(from, { target: { value: '2026-01-10' } })

    expect(onChange).toHaveBeenCalledWith({ ...filters, start: '2026-01-10' })
  })
})
