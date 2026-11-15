export type State = 'UP' | 'DOWN' | 'UNKNOWN' | 'PAUSED'

export interface User {
  id: number
  name: string
  email: string
  alert_email: string | null
  public_slug: string
}
export interface AuthResult { access_token: string; token_type: string; user: User }
export interface Monitor {
  id: number
  name: string
  url: string
  interval_seconds: number
  timeout_seconds: number
  expected_status: number
  sla_target: number
  alerts_enabled: boolean
  is_public: boolean
  is_paused: boolean
  state: State
  last_checked_at: string | null
  last_response_ms: number | null
  created_at: string
  uptime_pct: number | null
  total_checks: number
}
export type MonitorInput = Pick<Monitor, 'name' | 'url' | 'interval_seconds' | 'timeout_seconds' | 'expected_status' | 'sla_target' | 'alerts_enabled' | 'is_public'>
export interface Check {
  id: number; monitor_id: number; checked_at: string
  success: boolean; response_ms: number | null; status_code: number | null; error: string | null
}
export interface Incident {
  id: number; monitor_id: number; monitor_name: string; opened_at: string
  resolved_at: string | null; acknowledged_at: string | null; reason: string; status: 'OPEN' | 'RESOLVED'
}
export interface Notification {
  id: number; monitor_id: number | null; kind: string; title: string
  message: string; is_read: boolean; created_at: string
}
export interface Dashboard {
  total_monitors: number; uptime_pct: number | null; avg_response_ms: number | null
  open_incidents: number; total_checks: number
  status_counts: Record<State, number>
  timeline: Array<{ label: string; uptime: number | null; latency: number | null; checks: number }>
  recent_incidents: Incident[]; monitors: Monitor[]
}
export interface PublicStatus {
  workspace: string; updated_at: string; overall_state: 'DOWN' | 'OPERATIONAL' | 'UNKNOWN'
  monitors: Array<{ id: number; name: string; state: State; last_checked_at: string | null; uptime_pct: number | null }>
}
