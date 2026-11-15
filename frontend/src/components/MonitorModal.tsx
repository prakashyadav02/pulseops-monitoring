import { useState, type FormEvent } from 'react'
import { X } from 'lucide-react'
import type { Monitor, MonitorInput } from '../types'
import { ErrorBox } from './Shared'

const blank: MonitorInput = { name: '', url: 'https://', interval_seconds: 60, timeout_seconds: 10, expected_status: 200, sla_target: 99.9, alerts_enabled: true, is_public: true }

export default function MonitorModal({ monitor, onClose, onSave, busy }: { monitor?: Monitor | null; onClose: () => void; onSave: (value: MonitorInput) => Promise<void>; busy: boolean }) {
  const [form, setForm] = useState<MonitorInput>(monitor ? {
    name: monitor.name, url: monitor.url, interval_seconds: monitor.interval_seconds, timeout_seconds: monitor.timeout_seconds,
    expected_status: monitor.expected_status, sla_target: monitor.sla_target, alerts_enabled: monitor.alerts_enabled, is_public: monitor.is_public,
  } : blank)
  const [error, setError] = useState('')
  const update = <K extends keyof MonitorInput>(key: K, value: MonitorInput[K]) => setForm(prev => ({ ...prev, [key]: value }))
  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    try { await onSave(form) } catch (e) { setError((e as Error).message) }
  }
  return <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}><div className="modal-panel" role="dialog" aria-modal="true" aria-label={monitor ? 'Edit monitor' : 'Create monitor'}><div className="modal-top"><div><div className="eyebrow">ENDPOINT CONFIGURATION</div><h2>{monitor ? 'Edit monitor' : 'Add a new monitor'}</h2><p>We'll check your endpoint automatically and track its availability.</p></div><button className="icon-button" aria-label="Close" onClick={onClose}><X size={20}/></button></div>
    <form onSubmit={submit} className="modal-form"><label>Monitor name<input autoFocus required minLength={2} maxLength={120} value={form.name} onChange={e => update('name', e.target.value)} placeholder="e.g. Production API" /></label><label>Endpoint URL<input required type="url" value={form.url} onChange={e => update('url', e.target.value)} placeholder="https://api.example.com/health" /></label>
      <div className="form-grid"><label>Check interval<select value={form.interval_seconds} onChange={e => update('interval_seconds', Number(e.target.value))}><option value={30}>30 seconds</option><option value={60}>1 minute</option><option value={120}>2 minutes</option><option value={300}>5 minutes</option><option value={600}>10 minutes</option><option value={1800}>30 minutes</option><option value={3600}>1 hour</option></select></label><label>Timeout<select value={form.timeout_seconds} onChange={e => update('timeout_seconds', Number(e.target.value))}><option value={5}>5 seconds</option><option value={10}>10 seconds</option><option value={15}>15 seconds</option><option value={30}>30 seconds</option></select></label></div>
      <div className="form-grid"><label>Expected HTTP status<input type="number" min={100} max={599} required value={form.expected_status} onChange={e => update('expected_status', Number(e.target.value))} /></label><label>Monthly SLA target<select value={form.sla_target} onChange={e => update('sla_target', Number(e.target.value))}><option value={99}>99%</option><option value={99.5}>99.5%</option><option value={99.9}>99.9%</option><option value={99.95}>99.95%</option><option value={99.99}>99.99%</option><option value={100}>100%</option></select></label></div>
      <div className="modal-options"><label className="toggle-row"><span><strong>Incident alerts</strong><small>Create in-app alerts when the service goes down or recovers</small></span><input type="checkbox" checked={form.alerts_enabled} onChange={e => update('alerts_enabled', e.target.checked)} /></label><label className="toggle-row"><span><strong>Show on public status page</strong><small>Visitors can see this service's current status</small></span><input type="checkbox" checked={form.is_public} onChange={e => update('is_public', e.target.checked)} /></label></div>
      {error && <ErrorBox message={error} />}<p className="form-note">For safety, local/private IPs and nonstandard ports are blocked. Public HTTP(S) endpoints only.</p>
      <div className="modal-actions"><button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button><button type="submit" disabled={busy} className="btn btn-primary">{busy ? 'Saving...' : monitor ? 'Save changes' : 'Create monitor'}</button></div></form>
  </div></div>
}
