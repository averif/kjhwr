// All times are UTC; in January UK local time equals UTC.
const dateTime = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'UTC',
})
const shortDate = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })

export const formatDateTime = (iso: string) => dateTime.format(new Date(iso))
export const formatDate = (iso: string) => shortDate.format(new Date(iso))

export function formatMw(value: number | null | undefined): string {
  if (value === null || value === undefined) return '–'
  return `${Math.round(value).toLocaleString('en-GB')} MW`
}

export function formatGw(value: number): string {
  return `${(value / 1000).toLocaleString('en-GB', { maximumFractionDigits: 1 })} GW`
}

export const formatHour = (hour: number) => `${String(hour).padStart(2, '0')}:00`

// Axis maximum rounded up to a whole multiple of 5 GW (or 1 GW for small values) for clean ticks.
export const roundUp = (max: number) => {
  const step = max > 5000 ? 5000 : 1000
  return Math.ceil(max / step) * step
}
