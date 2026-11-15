import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { CheckCircle2, CircleHelp, Copy, ExternalLink, Globe2, XCircle } from 'lucide-react'
import { api } from '../api'
import { useAuth } from '../context'
import { ErrorBox, PageHeading, Spinner } from '../components/Shared'
import type { PublicStatus } from '../types'
import { pct, relativeDate } from '../utils'

export default function StatusPage({publicOnly=false}:{publicOnly?:boolean}) {
  const {slug: slugParam}=useParams()
  const {user}=useAuth()
  const slug=publicOnly?slugParam:user?.public_slug
  const {data,isLoading,error}=useQuery({queryKey:['publicStatus',slug],queryFn:()=>api<PublicStatus>(`/public/status/${slug}`),enabled:!!slug,refetchInterval:30000})
  const publicUrl=`${window.location.origin}/public/${slug}`
  const content=<><div className="public-status-hero"><div className={`public-status-symbol ${data?.overall_state==='DOWN'?'public-down':'public-up'}`}>{data?.overall_state==='DOWN'?<XCircle size={25}/>:data?.overall_state==='OPERATIONAL'?<CheckCircle2 size={25}/>:<CircleHelp size={25}/>}</div><div><h2>{data?.overall_state==='OPERATIONAL'?'All systems operational':data?.overall_state==='DOWN'?'Some systems are experiencing issues':'Waiting for live monitoring data'}</h2><p>Current status of public services • Updated {relativeDate(data?.updated_at ?? null)}</p></div></div><section className="panel public-services"><div className="section-heading"><div><h2>Service availability</h2><p>{data?.monitors.length ?? 0} publicly visible monitors</p></div><span className="legend-operational"><span/>Current status</span></div>{data?.monitors.length?<div className="public-service-list">{data.monitors.map(m=><div className="public-service" key={m.id}><div><span className={`service-status-dot ${m.state.toLowerCase()}`}/><strong>{m.name}</strong></div><div><span className="muted">30-day uptime: {pct(m.uptime_pct)}</span><span className={`public-service-state ${m.state.toLowerCase()}`}>{m.state==='UP'?'Operational':m.state==='DOWN'?'Outage':m.state==='PAUSED'?'Paused':'Pending'}</span></div></div>)}</div>:<div className="quiet-state"><Globe2 size={22}/>No public monitors are configured.</div>}</section></>
  if (publicOnly) return <div className="public-page"><header><div className="public-logo"><Globe2 size={22}/>PulseOps status</div><span>Public status page</span></header><div className="public-content"><div className="public-title"><div className="eyebrow">SERVICE HEALTH</div><h1>{data?.workspace ?? 'Status page'}</h1><p>Real-time updates on service availability.</p></div>{isLoading?<Spinner/>:error?<ErrorBox message={(error as Error).message}/>:content}</div><footer>Powered by PulseOps • Refreshes every 30 seconds</footer></div>
  return <><PageHeading eyebrow="TRANSPARENCY" title="Public status page" description="Share real-time service availability with your users." action={<a className="btn btn-secondary" href={publicUrl} target="_blank" rel="noreferrer">Open public page <ExternalLink size={16}/></a>}/><div className="share-bar"><div><Globe2 size={19}/><span><strong>Your public status link</strong><small>{publicUrl}</small></span></div><button className="btn btn-secondary btn-small" onClick={()=>navigator.clipboard.writeText(publicUrl)}><Copy size={15}/>Copy link</button></div>{isLoading?<Spinner/>:error?<ErrorBox message={(error as Error).message}/>:content}<p className="status-note">Only monitors marked "Show on public status page" are visible here. Private monitor URLs and incident details are not published.</p></>
}
