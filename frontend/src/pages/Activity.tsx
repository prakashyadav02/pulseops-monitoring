import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Activity as ActivityIcon, Bell, CheckCheck, CheckCircle2, Info, ShieldAlert } from 'lucide-react'
import { api } from '../api'
import { EmptyState, ErrorBox, PageHeading, Spinner } from '../components/Shared'
import type { Notification } from '../types'
import { dateFull } from '../utils'

export default function Activity() {
  const qc=useQueryClient()
  const {data,isLoading,error}=useQuery({queryKey:['notifications'],queryFn:()=>api<Notification[]>('/notifications'),refetchInterval:30000})
  const read=useMutation({mutationFn:()=>api<{ok:boolean}>('/notifications/read-all',{method:'POST'}),onSuccess:()=>qc.invalidateQueries({queryKey:['notifications']})})
  const unread=data?.filter(n=>!n.is_read).length ?? 0
  return <><PageHeading eyebrow="ACTIVITY CENTER" title="Alert inbox" description="A timeline of incidents, recoveries and important updates." action={<button className="btn btn-secondary" disabled={!unread||read.isPending} onClick={()=>read.mutate()}><CheckCheck size={17}/>Mark all as read</button>}/>
    <div className="panel activity-panel"><div className="section-heading"><div><h2>Notifications</h2><p>{unread} unread updates</p></div><div className="activity-count">{data?.length ?? 0} total</div></div>{isLoading?<Spinner/>:error?<ErrorBox message={(error as Error).message}/>:data?.length?<div className="notification-list">{data.map(n=>{const Icon=n.kind==='DOWN'?ShieldAlert:n.kind==='RECOVERY'?CheckCircle2:Info;return <div key={n.id} className={`notification-item ${n.is_read?'':'unread'}`}><div className={`notification-icon notification-${n.kind.toLowerCase()}`}><Icon size={20}/></div><div><div className="notification-title"><strong>{n.title}</strong>{!n.is_read&&<i/>}</div><p>{n.message}</p><small>{dateFull(n.created_at)}</small></div></div>})}</div>:<EmptyState icon={Bell} title="No notifications" description="Monitor alerts and service recovery messages will show up here."/>}</div><div className="activity-tip"><ActivityIcon size={18}/> Notifications are stored in the app. For real emails, configure SMTP settings in <code>backend/.env</code>.</div></>
}
