import type { Summary } from '../api'
import { formatMw } from '../format'

function biasNote(bias: number | null): string {
  if (bias === null) return ''
  if (Math.abs(bias) < 100) return 'Forecasts are roughly unbiased'
  return bias > 0 ? 'Forecasts tend to overestimate' : 'Forecasts tend to underestimate'
}

export default function StatCards({ summary }: { summary: Summary }) {
  const cards = [
    {
      label: 'Mean absolute error',
      value: formatMw(summary.maeMw),
      note: summary.nmaePct === null ? '' : `${summary.nmaePct}% of average wind output`,
    },
    {
      label: '90% of hours within',
      value: summary.p90AbsErrorMw === null ? '–' : `± ${formatMw(summary.p90AbsErrorMw)}`,
      note: 'Suggested procurement buffer',
    },
    {
      label: 'Average bias',
      value: summary.biasMw === null ? '–' : `${summary.biasMw > 0 ? '+' : ''}${formatMw(summary.biasMw)}`,
      note: biasNote(summary.biasMw),
    },
    {
      label: 'Worst hour',
      value: formatMw(summary.maxAbsErrorMw),
      note: `RMSE ${formatMw(summary.rmseMw)} · ${summary.count} hours`,
    },
  ]

  return (
    <div className="stat-cards">
      {cards.map((card) => (
        <div className="card stat" key={card.label}>
          <div className="stat-label">{card.label}</div>
          <div className="stat-value">{card.value}</div>
          <div className="stat-note">{card.note}</div>
        </div>
      ))}
    </div>
  )
}
