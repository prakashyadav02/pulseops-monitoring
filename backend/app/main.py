import asyncio
import csv
import io
from contextlib import asynccontextmanager, suppress
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import Integer as int_type, func, select
from sqlalchemy.orm import Session

from . import config
from .database import Base, engine, get_db
from .models import Check, Incident, Monitor, Notification, User, utcnow
from .schemas import (CheckOut, IncidentOut, LoginIn, MonitorIn, MonitorOut, MonitorPatch,
                      NotificationOut, ProfileOut, ProfilePatch, RegisterIn, TokenOut)
from .security import create_token, current_user, hash_password, new_slug, verify_password
from .seed import seed_demo
from .services import check_stats, run_monitor_check, scheduler_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if config.SEED_DEMO:
        seed_demo()
    stop = asyncio.Event()
    task = asyncio.create_task(scheduler_loop(stop)) if config.ENABLE_SCHEDULER else None
    try:
        yield
    finally:
        stop.set()
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(title='PulseOps Monitoring API', version='1.0.0', lifespan=lifespan,
              description='Full-stack HTTP uptime monitoring, incidents, SLA analytics, and alert inbox.')
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True,
                   allow_methods=['*'], allow_headers=['*'])


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'pulseops-api'}


def mine(db: Session, user: User, monitor_id: int) -> Monitor:
    monitor = db.get(Monitor, monitor_id)
    if not monitor or monitor.owner_id != user.id:
        raise HTTPException(status_code=404, detail='Monitor not found')
    return monitor


def monitor_output(db: Session, monitor: Monitor) -> MonitorOut:
    return MonitorOut.model_validate(monitor).model_copy(update=check_stats(db, monitor.id))


def incident_output(incident: Incident, monitor_name: str) -> IncidentOut:
    return IncidentOut.model_validate({**incident.__dict__, 'monitor_name': monitor_name})


@app.post('/api/auth/register', response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail='Email already registered')
    slug = new_slug()
    while db.scalar(select(User).where(User.public_slug == slug)):
        slug = new_slug()
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password), public_slug=slug)
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_token(user.id), user=ProfileOut.model_validate(user))


@app.post('/api/auth/login', response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Incorrect email or password')
    return TokenOut(access_token=create_token(user.id), user=ProfileOut.model_validate(user))


@app.get('/api/auth/me', response_model=ProfileOut)
def me(user: User = Depends(current_user)):
    return user


@app.patch('/api/settings', response_model=ProfileOut)
def update_settings(payload: ProfilePatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(user)
    return user


@app.get('/api/monitors', response_model=list[MonitorOut])
def list_monitors(user: User = Depends(current_user), db: Session = Depends(get_db)):
    monitors = db.scalars(select(Monitor).where(Monitor.owner_id == user.id).order_by(Monitor.created_at.desc())).all()
    return [monitor_output(db, m) for m in monitors]


@app.post('/api/monitors', response_model=MonitorOut, status_code=201)
def add_monitor(payload: MonitorIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    monitor = Monitor(owner_id=user.id, **payload.model_dump())
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor_output(db, monitor)


@app.get('/api/monitors/{monitor_id}', response_model=MonitorOut)
def get_monitor(monitor_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return monitor_output(db, mine(db, user, monitor_id))


@app.patch('/api/monitors/{monitor_id}', response_model=MonitorOut)
def edit_monitor(monitor_id: int, payload: MonitorPatch, user: User = Depends(current_user), db: Session = Depends(get_db)):
    monitor = mine(db, user, monitor_id)
    data = payload.model_dump(exclude_unset=True)
    # A changed URL is an unknown new service until rechecked.
    if 'url' in data and data['url'] != monitor.url:
        data.update(state='UNKNOWN', last_checked_at=None, last_response_ms=None)
        existing = db.scalars(select(Incident).where(Incident.monitor_id == monitor.id, Incident.status == 'OPEN')).all()
        for incident in existing:
            incident.status = 'RESOLVED'
            incident.resolved_at = utcnow()
    for key, value in data.items():
        setattr(monitor, key, value)
    db.commit()
    db.refresh(monitor)
    return monitor_output(db, monitor)


@app.delete('/api/monitors/{monitor_id}', status_code=204)
def delete_monitor(monitor_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    monitor = mine(db, user, monitor_id)
    # Notifications remain in the alert inbox; detach the deleted target.
    for notification in db.scalars(select(Notification).where(Notification.monitor_id == monitor.id)):
        notification.monitor_id = None
    db.delete(monitor)
    db.commit()
    return None


@app.post('/api/monitors/{monitor_id}/check')
async def check_now(monitor_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    m = mine(db, user, monitor_id)
    if m.is_paused:
        raise HTTPException(status_code=409, detail='Resume this monitor before checking')
    return await run_monitor_check(monitor_id)


@app.get('/api/monitors/{monitor_id}/checks', response_model=list[CheckOut])
def checks(monitor_id: int, limit: int = Query(default=75, ge=1, le=500),
           user: User = Depends(current_user), db: Session = Depends(get_db)):
    mine(db, user, monitor_id)
    return db.scalars(select(Check).where(Check.monitor_id == monitor_id).order_by(Check.checked_at.desc()).limit(limit)).all()


@app.get('/api/incidents', response_model=list[IncidentOut])
def incidents(status: str = Query(default='ALL', pattern='^(ALL|OPEN|RESOLVED)$'),
              user: User = Depends(current_user), db: Session = Depends(get_db)):
    statement = select(Incident, Monitor.name).join(Monitor).where(Monitor.owner_id == user.id)
    if status != 'ALL':
        statement = statement.where(Incident.status == status)
    rows = db.execute(statement.order_by(Incident.opened_at.desc()).limit(200)).all()
    return [incident_output(incident, name) for incident, name in rows]


@app.post('/api/incidents/{incident_id}/acknowledge', response_model=IncidentOut)
def acknowledge(incident_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.execute(select(Incident, Monitor.name).join(Monitor).where(Incident.id == incident_id, Monitor.owner_id == user.id)).first()
    if not row:
        raise HTTPException(status_code=404, detail='Incident not found')
    incident, name = row
    if incident.acknowledged_at is None:
        incident.acknowledged_at = utcnow()
        db.commit()
        db.refresh(incident)
    return incident_output(incident, name)


@app.get('/api/notifications', response_model=list[NotificationOut])
def notifications(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Notification).where(Notification.owner_id == user.id).order_by(Notification.created_at.desc()).limit(100)).all()


@app.post('/api/notifications/read-all')
def mark_all_read(user: User = Depends(current_user), db: Session = Depends(get_db)):
    for notification in db.scalars(select(Notification).where(Notification.owner_id == user.id, Notification.is_read.is_(False))):
        notification.is_read = True
    db.commit()
    return {'ok': True}


@app.get('/api/dashboard')
def dashboard(period: str = Query(default='24h', alias='range', pattern='^(24h|7d|30d)$'),
              user: User = Depends(current_user), db: Session = Depends(get_db)):
    monitors = db.scalars(select(Monitor).where(Monitor.owner_id == user.id)).all()
    ids = [m.id for m in monitors]
    duration = {'24h': timedelta(hours=24), '7d': timedelta(days=7), '30d': timedelta(days=30)}[period]
    cutoff = utcnow() - duration
    checks = db.scalars(select(Check).where(Check.monitor_id.in_(ids), Check.checked_at >= cutoff).order_by(Check.checked_at)).all() if ids else []
    successes = sum(c.success for c in checks)
    durations = [c.response_ms for c in checks if c.success and c.response_ms is not None]
    open_incidents = db.scalar(select(func.count(Incident.id)).join(Monitor).where(Monitor.owner_id == user.id, Incident.status == 'OPEN')) or 0
    bins = 24 if period == '24h' else (7 if period == '7d' else 30)
    bucket_seconds = duration.total_seconds() / bins
    bucket_data = [[] for _ in range(bins)]
    for check in checks:
        index = min(bins - 1, max(0, int((check.checked_at - cutoff).total_seconds() / bucket_seconds)))
        bucket_data[index].append(check)
    timeline = []
    for i, group in enumerate(bucket_data):
        timestamp = cutoff + timedelta(seconds=bucket_seconds * i)
        label = timestamp.strftime('%H:%M' if period == '24h' else '%b %d')
        p = round(100 * sum(c.success for c in group) / len(group), 1) if group else None
        latencies = [c.response_ms for c in group if c.success and c.response_ms is not None]
        timeline.append({'label': label, 'uptime': p, 'latency': round(sum(latencies) / len(latencies), 1) if latencies else None, 'checks': len(group)})
    recent_rows = db.execute(select(Incident, Monitor.name).join(Monitor).where(Monitor.owner_id == user.id).order_by(Incident.opened_at.desc()).limit(4)).all()
    status_counts = {'UP': sum(m.state == 'UP' and not m.is_paused for m in monitors),
                     'DOWN': sum(m.state == 'DOWN' and not m.is_paused for m in monitors),
                     'UNKNOWN': sum(m.state == 'UNKNOWN' and not m.is_paused for m in monitors),
                     'PAUSED': sum(m.is_paused for m in monitors)}
    return {
        'total_monitors': len(monitors), 'uptime_pct': round(100 * successes / len(checks), 2) if checks else None,
        'avg_response_ms': round(sum(durations) / len(durations), 1) if durations else None,
        'open_incidents': open_incidents, 'total_checks': len(checks), 'status_counts': status_counts,
        'timeline': timeline, 'recent_incidents': [incident_output(i, n) for i, n in recent_rows],
        'monitors': [monitor_output(db, m) for m in monitors],
    }


@app.get('/api/public/status/{slug}')
def public_status(slug: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.public_slug == slug))
    if not user:
        raise HTTPException(status_code=404, detail='Status page not found')
    monitors = db.scalars(select(Monitor).where(Monitor.owner_id == user.id, Monitor.is_public.is_(True)).order_by(Monitor.name)).all()
    return {
        'workspace': user.name, 'updated_at': utcnow(),
        'overall_state': 'DOWN' if any(m.state == 'DOWN' and not m.is_paused for m in monitors) else ('OPERATIONAL' if monitors and all(m.state == 'UP' and not m.is_paused for m in monitors) else 'UNKNOWN'),
        'monitors': [{'id': m.id, 'name': m.name, 'state': 'PAUSED' if m.is_paused else m.state,
                      'last_checked_at': m.last_checked_at, 'uptime_pct': check_stats(db, m.id)['uptime_pct']} for m in monitors],
    }


@app.get('/api/reports/sla.csv')
def sla_csv(days: int = Query(default=30, ge=1, le=90), user: User = Depends(current_user), db: Session = Depends(get_db)):
    """CSV export of sampled check-based uptime compared with each SLA target."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(['Monitor', 'URL', 'Window (days)', 'Total checks', 'Successful checks', 'Sampled uptime %', 'SLA target %', 'SLA met'])
    start = utcnow() - timedelta(days=days)
    monitors = db.scalars(select(Monitor).where(Monitor.owner_id == user.id).order_by(Monitor.name)).all()
    for m in monitors:
        total, success = db.execute(select(func.count(Check.id), func.sum(Check.success.cast(int_type))).where(Check.monitor_id == m.id, Check.checked_at >= start)).one()
        uptime = round(int(success or 0) * 100 / total, 2) if total else None
        # Prevent spreadsheet formula execution from user-authored service names.
        safe_name = "'" + m.name if m.name.startswith(('=', '+', '-', '@')) else m.name
        writer.writerow([safe_name, m.url, days, total or 0, int(success or 0), uptime if uptime is not None else 'N/A', m.sla_target,
                         'N/A' if uptime is None else 'Yes' if uptime >= m.sla_target else 'No'])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue()]), media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="pulseops-sla-report.csv"'})
