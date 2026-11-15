import type { State } from './types'

export function parseUTC(value: string): Date {
  return new Date(value.endsWith('Z') || /[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`)
}
export function relativeDate(value: string | null): string {
  if (!value) return 'Not checked yet'
  const diff = Math.max(0, Date.now() - parseUTC(value).getTime())
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}
export function dateFull(value: string | null): string {
  return value ? parseUTC(value).toLocaleString(undefined, { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'
}
export function pct(n: number | null, digits = 2): string { return n === null ? '—' : `${n.toFixed(digits)}%` }
export function millis(n: number | null): string { return n === null ? '—' : `${Math.round(n)} ms` }
export function stateLabel(state: State): string {
  return ({ UP: 'Operational', DOWN: 'Down', UNKNOWN: 'Pending', PAUSED: 'Paused' })[state]
}
export function initial(name: string): string { return name.trim().split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() }
export function domain(url: string): string { try { return new URL(url).hostname } catch { return url } }
