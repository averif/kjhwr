export const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export interface Filters {
  start: string
  end: string
  decisionHour: number
}

export interface Meta {
  firstDay: string
  lastDay: string
  defaultDecisionHour: number
}

export interface GenerationPoint {
  time: string
  actual: number | null
  forecast: number | null
  publishTime: string | null
}

export interface Summary {
  count: number
  maeMw: number | null
  rmseMw: number | null
  biasMw: number | null
  nmaePct: number | null
  p90AbsErrorMw: number | null
  maxAbsErrorMw: number | null
}

export interface DailyError {
  date: string
  maeMw: number
  biasMw: number
}

export interface HorizonBucket {
  horizonHours: number
  maeMw: number
  count: number
}

export function buildQuery(filters: Filters, includeDecisionHour = true): string {
  const params = new URLSearchParams({ start: filters.start, end: filters.end })
  if (includeDecisionHour) params.set('decision_hour', String(filters.decisionHour))
  return params.toString()
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`)
  if (!response.ok) throw new Error(`Request failed (${response.status}): ${path}`)
  return response.json() as Promise<T>
}

export const fetchMeta = () => getJson<Meta>('/api/meta')

export const fetchGeneration = (filters: Filters) =>
  getJson<{ points: GenerationPoint[] }>(`/api/generation?${buildQuery(filters)}`)

export const fetchAccuracy = (filters: Filters) =>
  getJson<{ summary: Summary; daily: DailyError[] }>(`/api/accuracy?${buildQuery(filters)}`)

export const fetchHorizon = (filters: Filters) =>
  getJson<{ buckets: HorizonBucket[] }>(`/api/accuracy/horizon?${buildQuery(filters, false)}`)
