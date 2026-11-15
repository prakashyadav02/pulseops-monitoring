import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Activity, Bell, ChevronDown, CircleHelp, ExternalLink, Gauge, Globe2, LayoutDashboard, LogOut, Menu, Settings2, ShieldAlert, X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api'
import { useAuth } from '../context'
import type { Notification } from '../types'
import { initial } from '../utils'

const navigation = [
  { label: 'Overview', path: '/', icon: LayoutDashboard },
  { label: 'Monitors', path: '/monitors', icon: Gauge },
  { label: 'Incidents', path: '/incidents', icon: ShieldAlert },
  { label: 'Activity', path: '/activity', icon: Activity },
  { label: 'Status page', path: '/status', icon: Globe2 },
]

export function Brand() { return <div className="brand"><div className="brand-icon"><Activity size={21} strokeWidth={2.6} /></div><span>pulse<span className="brand-light">ops</span></span><span className="brand-dot">.</span></div> }

export default function Layout() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const { data: notifications } = useQuery({ queryKey: ['notifications'], queryFn: () => api<Notification[]>('/notifications'), refetchInterval: 30000 })
  const unread = notifications?.filter(n => !n.is_read).length ?? 0
  return <div className="app-shell">
    {mobileOpen && <div className="mobile-overlay" onClick={() => setMobileOpen(false)} />}
    <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
      <div className="sidebar-head"><Brand /><button className="icon-button mobile-close" onClick={() => setMobileOpen(false)} aria-label="Close menu"><X size={19} /></button></div>
      <div className="workspace-picker"><div className="workspace-emblem">P</div><div className="workspace-name"><strong>Personal workspace</strong><span>Free plan</span></div><ChevronDown size={15} /></div>
      <div className="sidebar-label">MONITORING</div>
      <nav className="navigation">{navigation.map(({label, path, icon: Icon}) => <NavLink key={path} to={path} end={path === '/'} onClick={() => setMobileOpen(false)} className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}><Icon size={19} strokeWidth={1.9}/><span>{label}</span>{label === 'Activity' && unread > 0 && <span className="nav-count">{unread}</span>}</NavLink>)}</nav>
      <div className="sidebar-label tools-label">WORKSPACE</div>
      <nav className="navigation"><NavLink to="/settings" onClick={() => setMobileOpen(false)} className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}><Settings2 size={19} strokeWidth={1.9}/>Settings</NavLink></nav>
      <div className="sidebar-bottom"><div className="help-card"><div className="help-icon"><CircleHelp size={19}/></div><h4>Always in the know.</h4><p>Monitor your endpoints and respond before users notice.</p><a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">API documentation <ExternalLink size={13} /></a></div>
        <div className="sidebar-profile" onClick={() => setMenuOpen(!menuOpen)} role="button" tabIndex={0} onKeyDown={e => e.key === 'Enter' && setMenuOpen(!menuOpen)}><div className="avatar">{initial(user?.name ?? 'U')}</div><div className="profile-text"><strong>{user?.name}</strong><span>{user?.email}</span></div><ChevronDown size={16}/></div>
        {menuOpen && <button className="logout-menu" onClick={() => {signOut(); navigate('/login')}}><LogOut size={16}/> Sign out</button>}
      </div>
    </aside>
    <div className="main-shell">
      <header className="topbar"><div className="topbar-left"><button className="mobile-menu icon-button" onClick={() => setMobileOpen(true)} aria-label="Open menu"><Menu size={21}/></button><span className="breadcrumb">Workspace</span><span className="breadcrumb-slash">/</span><span className="breadcrumb-current">Monitoring</span></div><div className="topbar-right"><span className="live-indicator"><span/>Live monitoring</span><button className="top-icon" onClick={() => navigate('/activity')} aria-label="Notifications"><Bell size={19}/>{unread > 0 && <i/>}</button><button className="top-avatar" onClick={() => navigate('/settings')}>{initial(user?.name ?? 'U')}</button></div></header>
      <main className="main-content"><Outlet /></main>
      <footer className="site-footer"><span>© 2026 PulseOps • Built with FastAPI + React</span><span><span className="footer-dot" /> System updates every 30 seconds</span></footer>
    </div>
  </div>
}
