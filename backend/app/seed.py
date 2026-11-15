from datetime import timedelta
from sqlalchemy import select
from .database import SessionLocal
from .models import User, Monitor, Check, Incident, Notification, utcnow
from .security import hash_password


def seed_demo():
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == 'demo@pulseops.dev')):
            return
        user = User(name='Alex Morgan', email='demo@pulseops.dev', password_hash=hash_password('Demo@12345'), public_slug='demo-workspace')
        db.add(user)
        db.flush()
        targets = [
            ('Website', 'https://example.com', 76, 99.6),
            ('GitHub API', 'https://api.github.com', 120, 99.9),
            ('Python Docs', 'https://www.python.org', 91, 100.0),
            ('Vite Website', 'https://vite.dev', 132, 98.8),
        ]
        now = utcnow()
        for index, (name, url, ms, uptime) in enumerate(targets):
            m = Monitor(owner_id=user.id, name=name, url=url, interval_seconds=60, timeout_seconds=10,
                        state='UP', last_response_ms=ms, last_checked_at=now - timedelta(minutes=2), is_public=True)
            db.add(m)
            db.flush()
            # Illustrative history gives a useful dashboard on first launch.
            for i in range(48):
                bad = (index == 3 and i in (6, 7)) or (index == 0 and i == 10)
                db.add(Check(monitor_id=m.id, checked_at=now - timedelta(minutes=(48-i) * 30),
                             success=not bad, response_ms=ms + (i % 7) * 9 + index * 3,
                             status_code=503 if bad else 200, error='Service unavailable' if bad else None))
            if index == 3:
                incident = Incident(monitor_id=m.id, opened_at=now - timedelta(hours=21),
                                    resolved_at=now - timedelta(hours=20), reason='HTTP 503 Service Unavailable', status='RESOLVED')
                db.add(incident)
        db.add(Notification(owner_id=user.id, kind='RECOVERY', title='Vite Website recovered',
                            message='Vite Website is back online after a 1-hour incident.', created_at=now - timedelta(hours=20)))
        db.add(Notification(owner_id=user.id, kind='INFO', title='Welcome to PulseOps',
                            message='This demo workspace includes illustrative history. Live HTTP monitoring runs automatically.', created_at=now))
        db.commit()
