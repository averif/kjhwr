import type { Filters, Meta } from '../api'
import { formatHour } from '../format'

interface Props {
  meta: Meta
  filters: Filters
  onChange: (filters: Filters) => void
}

const HOURS = Array.from({ length: 24 }, (_, hour) => hour)

export default function Controls({ meta, filters, onChange }: Props) {
  return (
    <div className="controls">
      <label>
        From
        <input
          type="date"
          value={filters.start}
          min={meta.firstDay}
          max={filters.end}
          onChange={(e) => e.target.value && onChange({ ...filters, start: e.target.value })}
        />
      </label>
      <label>
        To
        <input
          type="date"
          value={filters.end}
          min={filters.start}
          max={meta.lastDay}
          onChange={(e) => e.target.value && onChange({ ...filters, end: e.target.value })}
        />
      </label>
      <label>
        Decision time (D-1, UTC)
        <select
          value={filters.decisionHour}
          onChange={(e) => onChange({ ...filters, decisionHour: Number(e.target.value) })}
        >
          {HOURS.map((hour) => (
            <option key={hour} value={hour}>
              {formatHour(hour)}
              {hour === meta.defaultDecisionHour ? ' (auction close)' : ''}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
