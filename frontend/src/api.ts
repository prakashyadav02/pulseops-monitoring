const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('pulseops_token')
  const response = await fetch(`${API_BASE}/api${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  })
  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const payload = await response.json()
      if (typeof payload.detail === 'string') detail = payload.detail
      if (Array.isArray(payload.detail)) detail = payload.detail.map((e: { msg?: string }) => e.msg ?? 'Invalid input').join('; ')
    } catch { /* non-JSON error */ }
    throw new Error(detail)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const json = (method: string, value?: unknown): RequestInit => ({
  method,
  ...(value !== undefined ? { body: JSON.stringify(value) } : {}),
})


export async function downloadSlaReport(days = 30): Promise<void> {
  const token = localStorage.getItem('pulseops_token')
  const response = await fetch(`${API_BASE}/api/reports/sla.csv?days=${days}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!response.ok) throw new Error('Unable to download SLA report')
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'pulseops-sla-report.csv'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
