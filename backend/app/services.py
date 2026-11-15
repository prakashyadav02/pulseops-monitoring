import asyncio
import smtplib
import time
from datetime import datetime, timedelta
from email.message import EmailMessage

import httpx
from sqlalchemy import func, select
from . import config
from .database import SessionLocal
from .models import Check, Incident, Monitor, Notification, User, utcnow
from .security import ensure_public_dns


def check_stats(db, monitor_id: int, days: int = 30) -> dict:
    since = utcnow() - timedelta(days=days)
    total, success = db.execute(select(func.count(Check.id), func.sum(Check.success.cast(IntegerBool))).where(Check.monitor_id == monitor_id, Check.checked_at >= since)).one()
    return {'total_checks': int(total or 0), 'uptime_pct': round(100 * int(success or 0) / total, 2) if total else None}


# SQLAlchemy CAST works with SQLite and PostgreSQL, unlike boolean sums on some DBs.
from sqlalchemy import Integer as IntegerBool


async def probe(url: str, timeout_seconds: int, expected_status: int) -> tuple[bool, int | None, float | None, str | None]:
    start = time.perf_counter()
    try:
        # DNS guard applies to every check, not merely on monitor creation.
        await asyncio.to_thread(ensure_public_dns, url)
        # Do not follow redirects to a private/internal URL.
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False, trust_env=False) as client:
            response = await client.get(url, headers={'User-Agent': 'PulseOps/1.0 (monitoring)'})
        ms = round((time.perf_counter() - start) * 1000, 1)
        ok = response.status_code == expected_status
        return ok, response.status_code, ms, None if ok else f'Expected HTTP {expected_status}; received {response.status_code}'
    except Exception as exc:
        return False, None, round((time.perf_counter() - start) * 1000, 1), str(exc)[:300]


def _email_alert(address: str, title: str, message: str):
    if not (config.SMTP_HOST and config.SMTP_FROM):
        return
    mail = EmailMessage()
    mail['Subject'] = f'[PulseOps] {title}'
    mail['From'] = config.SMTP_FROM
    mail['To'] = address
    mail.set_content(message)
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10) as smtp:
        if config.SMTP_STARTTLS:
            smtp.starttls()
        if config.SMTP_USERNAME:
            smtp.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        smtp.send_message(mail)


async def run_monitor_check(monitor_id: int) -> dict | None:
    """Probe without holding the DB session; then atomically record state change."""
    with SessionLocal() as db:
        monitor = db.get(Monitor, monitor_id)
        if not monitor or monitor.is_paused:
            return None
        url, timeout, expected = monitor.url, monitor.timeout_seconds, monitor.expected_status
    success, code, latency, error = await probe(url, timeout, expected)
    email_payload = None
    with SessionLocal() as db:
        monitor = db.get(Monitor, monitor_id)
        if not monitor or monitor.is_paused:
            return None
        now = utcnow()
        previous = monitor.state
        db.add(Check(monitor_id=monitor.id, checked_at=now, success=success, response_ms=latency, status_code=code, error=error))
        monitor.state = 'UP' if success else 'DOWN'
        monitor.last_response_ms = latency
        monitor.last_checked_at = now
        open_incident = db.scalar(select(Incident).where(Incident.monitor_id == monitor.id, Incident.status == 'OPEN').order_by(Incident.id.desc()))
        notification = None
        if not success and open_incident is None:
            db.add(Incident(monitor_id=monitor.id, opened_at=now, reason=error or 'HTTP probe failed', status='OPEN'))
            notification = ('DOWN', f'{monitor.name} is down', f'{monitor.name}: {error or "Unsuccessful health check"}')
        elif success and open_incident is not None:
            open_incident.status = 'RESOLVED'
            open_incident.resolved_at = now
            notification = ('RECOVERY', f'{monitor.name} recovered', f'{monitor.name} is responding with HTTP {code} again.')
        if notification and monitor.alerts_enabled:
            kind, title, message = notification
            db.add(Notification(owner_id=monitor.owner_id, monitor_id=monitor.id, kind=kind, title=title, message=message))
            user = db.get(User, monitor.owner_id)
            if user and user.alert_email:
                email_payload = (user.alert_email, title, message)
        db.commit()
    if email_payload:
        try:
            await asyncio.to_thread(_email_alert, *email_payload)
        except Exception as exc:
            # SMTP misconfiguration should not lose monitoring checks/incidents.
            print(f'[PulseOps] Optional email delivery failed: {exc}')
    return {'monitor_id': monitor_id, 'state': 'UP' if success else 'DOWN', 'status_code': code, 'response_ms': latency, 'error': error, 'previous_state': previous}


async def scheduler_loop(stop: asyncio.Event):
    # One scheduler per process. Use a dedicated scheduler / worker + leader lock
    # for production or multi-worker deployment.
    semaphore = asyncio.Semaphore(5)
    in_flight: set[int] = set()

    async def checked(mid: int):
        async with semaphore:
            try:
                await run_monitor_check(mid)
            except Exception as exc:
                print(f'[PulseOps] Monitor {mid} check error: {exc}')
            finally:
                in_flight.discard(mid)

    running: set[asyncio.Task] = set()
    while not stop.is_set():
        now = utcnow()
        with SessionLocal() as db:
            monitors = db.scalars(select(Monitor).where(Monitor.is_paused.is_(False))).all()
            due = [m.id for m in monitors if m.id not in in_flight and (m.last_checked_at is None or (now - m.last_checked_at).total_seconds() >= m.interval_seconds)]
        for mid in due[:50]:
            in_flight.add(mid)
            task = asyncio.create_task(checked(mid))
            running.add(task)
            task.add_done_callback(running.discard)
        try:
            await asyncio.wait_for(stop.wait(), timeout=config.SCHEDULER_POLL_SECONDS)
        except asyncio.TimeoutError:
            pass
    if running:
        await asyncio.gather(*running, return_exceptions=True)
