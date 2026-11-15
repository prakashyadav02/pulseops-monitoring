import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircle, Check, CheckCircle2, Clock3, ShieldCheck } from 'lucide-react'
import { api } from '../api'
import { EmptyState, ErrorBox, PageHeading, Spinner } from '../components/Shared'
import type { Incident } from '../types'
import { dateFull, relativeDate } from '../utils'

export default function Incidents() {
  const [filter, setFilter] = useState<'ALL'|'OPEN'|'RESOLVED'>('ALL')
  const qc = useQueryClient()
  const {data: allIncidents, isLoading, error} = useQuery({queryKey:['incidents','ALL'],queryFn:()=>api<Incident[]>('/incidents?status=ALL'),refetchInterval:30000})
  const data = allIncidents?.filter(i => filter === 'ALL' || i.status === filter)
  const ack = useMutation({mutationFn:(id:number)=>api<Incident>(`/incidents/${id}/acknowledge`,{method:'POST'}),onSuccess:()=>{qc.invalidateQueries({queryKey:['incidents']});qc.invalidateQueries({queryKey:['dashboard']})}})
  return <><PageHeading eyebrow="RESPONSE" title="Incident management" description="Investigate service failures and track recovery."/>
    <div className="incident-summary"><div><span className="incident-icon-active"><AlertCircle size={19}/></span><span>Open incidents</span><strong>{allIncidents?.filter(i=>i.status==='OPEN').length ?? '—'}</strong></div><div><span className="incident-icon-closed"><ShieldCheck size={19}/></span><span>Shown incidents</span><strong>{data?.length ?? '—'}</strong></div></div>
    <div className="panel"><div className="list-toolbar"><div className="pill-tabs">{(['ALL','OPEN','RESOLVED'] as const).map(s=><button key={s} className={filter===s?'pill-selected':''} onClick={()=>setFilter(s)}>{s==='ALL'?'All incidents':s==='OPEN'?'Open':'Resolved'}</button>)}</div></div>{ack.error&&<ErrorBox message={ack.error.message}/>}{isLoading?<Spinner/>:error?<ErrorBox message={(error as Error).message}/>:data?.length?<div className="incident-full-list">{data.map(i=><div className="incident-item" key={i.id}><div className={`incident-big-icon ${i.status==='OPEN'?'incident-open':'incident-resolved'}`}>{i.status==='OPEN'?<AlertCircle size={22}/>:<CheckCircle2 size={22}/>}</div><div className="incident-item-main"><div className="incident-item-title"><h3>{i.monitor_name}</h3><span className={i.status==='OPEN'?'incident-state-open':'incident-state-resolved'}>{i.status==='OPEN'?'Active incident':'Resolved'}</span>{i.acknowledged_at&&<span className="incident-acked"><Check size={12}/> Acknowledged</span>}</div><p>{i.reason}</p><div className="incident-meta"><span><Clock3 size={14}/>Started {dateFull(i.opened_at)}</span>{i.resolved_at&&<span>Recovered {dateFull(i.resolved_at)}</span>}</div></div><div className="incident-item-right"><span className="muted">{relativeDate(i.opened_at)}</span>{i.status==='OPEN'&&!i.acknowledged_at&&<button className="btn btn-secondary btn-small" disabled={ack.isPending} onClick={()=>ack.mutate(i.id)}>Acknowledge</button>}</div></div>)}</div>:<EmptyState icon={CheckCircle2} title="No incidents found" description={filter==='OPEN'?'All monitored services are currently clear of open incidents.':'When a monitored service goes down, an incident appears here automatically.'}/>}</div></>
}
