import type { ReactNode } from 'react'
import { Activity, ArrowUpRight, CheckCircle2, CircleHelp, PauseCircle, XCircle, type LucideIcon } from 'lucide-react'
import type { State } from '../types'
import { stateLabel } from '../utils'

export function StatusBadge({ state }: { state: State }) {
  const Icon: LucideIcon = state === 'UP' ? CheckCircle2 : state === 'DOWN' ? XCircle : state === 'PAUSED' ? PauseCircle : CircleHelp
  return <span className={`state-badge badge-${state.toLowerCase()}`}><Icon size={13} strokeWidth={2.3} />{stateLabel(state)}</span>
}
export function PageHeading({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow ?? 'WORKSPACE'}</div><h1>{title}</h1>{description && <p>{description}</p>}</div>{action && <div className="heading-action">{action}</div>}</div>
}
export function EmptyState({ icon: Icon = Activity, title, description, action }: { icon?: LucideIcon; title: string; description: string; action?: ReactNode }) {
  return <div className="empty-state"><div className="empty-icon"><Icon size={24} /></div><h3>{title}</h3><p>{description}</p>{action}</div>
}
export function SectionHeading({ title, subtitle, linkText, onLink }: { title: string; subtitle?: string; linkText?: string; onLink?: () => void }) {
  return <div className="section-heading"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{linkText && <button className="link-button" onClick={onLink}>{linkText} <ArrowUpRight size={15} /></button>}</div>
}
export function Spinner() { return <div className="loading"><div className="spinner" />Loading workspace...</div> }
export function ErrorBox({ message }: { message: string }) { return <div className="error-message">{message}</div> }
