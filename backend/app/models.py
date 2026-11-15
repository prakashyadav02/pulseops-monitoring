from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def utcnow():
    # Store naive UTC values in SQLite to keep dates sortable across SQLite / Postgres.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    alert_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    public_slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    monitors: Mapped[list['Monitor']] = relationship(back_populates='owner', cascade='all, delete-orphan')


class Monitor(Base):
    __tablename__ = 'monitors'
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    url: Mapped[str] = mapped_column(String(2048))
    interval_seconds: Mapped[int] = mapped_column(Integer, default=60)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=10)
    expected_status: Mapped[int] = mapped_column(Integer, default=200)
    sla_target: Mapped[float] = mapped_column(Float, default=99.9)
    alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    state: Mapped[str] = mapped_column(String(12), default='UNKNOWN')
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_response_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    owner: Mapped[User] = relationship(back_populates='monitors')
    checks: Mapped[list['Check']] = relationship(back_populates='monitor', cascade='all, delete-orphan')
    incidents: Mapped[list['Incident']] = relationship(back_populates='monitor', cascade='all, delete-orphan')


class Check(Base):
    __tablename__ = 'checks'
    id: Mapped[int] = mapped_column(primary_key=True)
    monitor_id: Mapped[int] = mapped_column(ForeignKey('monitors.id'), index=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    success: Mapped[bool] = mapped_column(Boolean)
    response_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    monitor: Mapped[Monitor] = relationship(back_populates='checks')


class Incident(Base):
    __tablename__ = 'incidents'
    id: Mapped[int] = mapped_column(primary_key=True)
    monitor_id: Mapped[int] = mapped_column(ForeignKey('monitors.id'), index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    reason: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default='OPEN')
    monitor: Mapped[Monitor] = relationship(back_populates='incidents')


class Notification(Base):
    __tablename__ = 'notifications'
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    monitor_id: Mapped[int | None] = mapped_column(ForeignKey('monitors.id', ondelete='SET NULL'), nullable=True)
    kind: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(180))
    message: Mapped[str] = mapped_column(String(1000))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
