from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class FromORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ProfileOut(FromORM):
    id: int
    name: str
    email: EmailStr
    alert_email: EmailStr | None
    public_slug: str


class ProfilePatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    alert_email: EmailStr | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: ProfileOut


class MonitorIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    url: str = Field(min_length=8, max_length=2048)
    interval_seconds: int = Field(default=60, ge=30, le=86400)
    timeout_seconds: int = Field(default=10, ge=2, le=30)
    expected_status: int = Field(default=200, ge=100, le=599)
    sla_target: float = Field(default=99.9, ge=90, le=100)
    alerts_enabled: bool = True
    is_public: bool = True

    @field_validator('url')
    @classmethod
    def url_must_be_http(cls, value: str) -> str:
        from .security import validate_target_url
        validate_target_url(value)
        return value.strip()


class MonitorPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    url: str | None = Field(default=None, min_length=8, max_length=2048)
    interval_seconds: int | None = Field(default=None, ge=30, le=86400)
    timeout_seconds: int | None = Field(default=None, ge=2, le=30)
    expected_status: int | None = Field(default=None, ge=100, le=599)
    sla_target: float | None = Field(default=None, ge=90, le=100)
    alerts_enabled: bool | None = None
    is_public: bool | None = None
    is_paused: bool | None = None

    @field_validator('url')
    @classmethod
    def url_must_be_http(cls, value: str | None) -> str | None:
        if value is not None:
            from .security import validate_target_url
            validate_target_url(value)
        return value.strip() if value else value


class MonitorOut(FromORM):
    id: int
    name: str
    url: str
    interval_seconds: int
    timeout_seconds: int
    expected_status: int
    sla_target: float
    alerts_enabled: bool
    is_public: bool
    is_paused: bool
    state: str
    last_checked_at: datetime | None
    last_response_ms: float | None
    created_at: datetime
    uptime_pct: float | None = None
    total_checks: int = 0


class CheckOut(FromORM):
    id: int
    monitor_id: int
    checked_at: datetime
    success: bool
    response_ms: float | None
    status_code: int | None
    error: str | None


class IncidentOut(FromORM):
    id: int
    monitor_id: int
    monitor_name: str
    opened_at: datetime
    resolved_at: datetime | None
    acknowledged_at: datetime | None
    reason: str
    status: str


class NotificationOut(FromORM):
    id: int
    monitor_id: int | None
    kind: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
