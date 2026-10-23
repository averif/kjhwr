import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { GenerationPoint } from '../api'
import { formatDate, formatDateTime, formatGw, formatMw, roundUp } from '../format'

interface TooltipProps {
  active?: boolean
  payload?: { payload: GenerationPoint }[]
}

function GenerationTooltip({ active, payload }: TooltipProps) {
  const point = payload?.[0]?.payload
  if (!active || !point) return null
  return (
    <div className="tooltip">
      <strong>{formatDateTime(point.time)}</strong>
      <div><span className="swatch actual" /> Actual: {formatMw(point.actual)}</div>
      {point.forecast !== null && (
        <>
          <div><span className="swatch forecast" /> Forecast: {formatMw(point.forecast)}</div>
          <div className="muted">Published {formatDateTime(point.publishTime!)}</div>
        </>
      )}
    </div>
  )
}

export default function GenerationChart({ points }: { points: GenerationPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={340}>
      <LineChart data={points} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis
          dataKey="time"
          tickFormatter={formatDate}
          minTickGap={40}
          stroke="var(--axis)"
          tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
        />
        <YAxis
          domain={[0, roundUp]}
          tickCount={6}
          tickFormatter={formatGw}
          width={56}
          stroke="var(--axis)"
          tick={{ fill: 'var(--text-muted)', fontSize: 12 }}
        />
        <Tooltip content={<GenerationTooltip />} />
        <Legend verticalAlign="top" align="right" height={32} iconType="plainline" />
        <Line name="Actual" dataKey="actual" stroke="var(--series-1)" strokeWidth={2} dot={false} connectNulls isAnimationActive={false} />
        <Line name="Day-ahead forecast" dataKey="forecast" stroke="var(--series-2)" strokeWidth={2} dot={false} connectNulls isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
