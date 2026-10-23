import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { formatGw, formatMw } from '../format'

export interface BarDatum {
  label: string
  tooltip: string
  maeMw: number
}

// Single-series MAE bar chart shared by the daily-error and horizon views.
export default function BarChartCard({ bars }: { bars: BarDatum[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={bars} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} barCategoryGap={2}>
        <CartesianGrid stroke="var(--grid)" vertical={false} />
        <XAxis dataKey="label" minTickGap={16} stroke="var(--axis)" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
        <YAxis tickFormatter={formatGw} width={56} stroke="var(--axis)" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
        <Tooltip
          cursor={{ fill: 'var(--hover)' }}
          content={({ active, payload }) => {
            const bar = payload?.[0]?.payload as BarDatum | undefined
            if (!active || !bar) return null
            return (
              <div className="tooltip">
                <strong>{bar.tooltip}</strong>
                <div>MAE: {formatMw(bar.maeMw)}</div>
              </div>
            )
          }}
        />
        <Bar dataKey="maeMw" fill="var(--series-1)" radius={[4, 4, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  )
}
