import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity, ArrowRight, CheckCircle2, ShieldCheck, Zap } from 'lucide-react'
import { api, json } from '../api'
import { useAuth } from '../context'
import { Brand } from '../components/Layout'
import { ErrorBox } from '../components/Shared'
import type { AuthResult } from '../types'

export default function Login() {
  const navigate = useNavigate()
  const { signIn } = useAuth()
  const [register, setRegister] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  async function submit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError('')
    try {
      const result = await api<AuthResult>(register ? '/auth/register' : '/auth/login', json('POST', register ? { name, email, password } : { email, password }))
      signIn(result); navigate('/')
    } catch (e) { setError((e as Error).message) } finally { setLoading(false) }
  }
  function demo() { setEmail('demo@pulseops.dev'); setPassword('Demo@12345'); setRegister(false); setError('') }
  return <div className="auth-page"><section className="auth-left"><div className="auth-brand"><Brand/></div><div className="auth-hero"><div className="hero-kicker"><span className="pulse-dot"/> THE MONITORING PLATFORM FOR BUILDERS</div><h1>Know first.<br/><span>Fix faster.</span></h1><p>Track your infrastructure with simple, beautiful monitoring. Stay ahead of incidents and give users the reliability they deserve.</p><div className="auth-features"><div><CheckCircle2 size={19}/>Real-time uptime & latency tracking</div><div><Zap size={19}/>Instant incidents and recovery alerts</div><div><ShieldCheck size={19}/>Transparent public status pages</div></div></div><div className="auth-visual"><div className="auth-glow"/><div className="auth-mini-card"><div className="auth-mini-top"><span className="mini-logo"><Activity size={15}/></span> Production health <span className="mini-live">● Live</span></div><div className="auth-mini-numbers"><strong>99.98<span>%</span></strong><small>Uptime this month</small></div><div className="mini-bars">{Array.from({length: 36}, (_,i) => <i key={i} style={{ height: `${26 + Math.abs(Math.sin(i*2.4))*39}%`, opacity: i === 23 ? .5 : 1 }}/>)}</div><div className="auth-mini-footer"><span>● All systems operational</span><span>24 hours <ArrowRight size={13}/></span></div></div></div><div className="auth-left-footer">© 2026 PulseOps. Made for reliable systems.</div></section>
  <section className="auth-right"><div className="auth-form-wrap"><div className="auth-mobile-brand"><Brand/></div><div className="auth-welcome"><div className="eyebrow">WELCOME TO PULSEOPS</div><h2>{register ? 'Create your account' : 'Welcome back'}</h2><p>{register ? 'Start monitoring your first endpoint in minutes.' : 'Sign in to access your monitoring workspace.'}</p></div><form onSubmit={submit} className="auth-form">{register && <label>Full name<input autoFocus required minLength={2} value={name} onChange={e => setName(e.target.value)} placeholder="Alex Morgan" /></label>}<label>Email address<input autoFocus={!register} required type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" /></label><label>Password<input required minLength={register ? 8 : 1} type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter your password" /></label>{error && <ErrorBox message={error}/>}<button type="submit" className="btn btn-primary auth-submit" disabled={loading}>{loading ? 'Please wait...' : register ? 'Create account' : 'Sign in to dashboard'}<ArrowRight size={17}/></button></form><div className="auth-switch">{register ? 'Already have an account?' : 'New to PulseOps?'} <button onClick={() => {setRegister(!register); setError('')}}>{register ? 'Sign in' : 'Create an account'}</button></div><div className="auth-divider"><span>OR TRY THE DEMO</span></div><button className="demo-btn" onClick={demo}><span className="demo-icon"><Zap size={18}/></span><span><strong>Explore demo workspace</strong><small>Use the prefilled credentials to sign in</small></span><ArrowRight size={18}/></button><div className="auth-hint">Demo credentials: <strong>demo@pulseops.dev</strong> / <strong>Demo@12345</strong></div></div></section></div>
}
