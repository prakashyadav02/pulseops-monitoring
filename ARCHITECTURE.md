# PulseOps architecture and evolution

## What happens when you click Add monitor

```text
React (Vite + TypeScript)
        |
        | HTTPS/HTTP JSON request (JWT bearer token)
        v
FastAPI REST endpoints
        |-- JWT + Argon2 authentication
        |-- Pydantic input validation
        |-- SQLAlchemy ORM -> SQLite (or PostgreSQL via DATABASE_URL)
        |-- Public status & SLA CSV exports
        |
        v
Single-process asynchronous scheduler (every ~15s poll)
        |
        | due according to monitor.interval_seconds, max 5 concurrent probes
        v
HTTP probe (DNS validation; no redirects; timeout)
        |
        | success / error / status / elapsed time
        v
Check history -> Monitor state -> Incident state transition
                                        |
                                        v
                              In-app notification
                                        |
                                        v
                            Optional SMTP email alert
```

### State transitions

- New monitor: `UNKNOWN` until the first check.
- Successful check: `UP` (and resolve any open incident).
- Failed check: `DOWN` (and create an incident only if one isn't already open).
- Each new open incident or recovery produces an in-app alert if `alerts_enabled`.
- Paused monitors are skipped by the scheduler and display `PAUSED` in the frontend.
- A changed URL is a new target: monitoring state resets and the previous open incident is closed.

### Data model

- `users (id, email, name, password_hash, alert_email, public_slug)`
- `monitors (id, owner_id, name, url, interval_seconds, timeout_seconds, expected_status, sla_target, is_paused, state, last_checked_at, ...)`
- `checks (id, monitor_id, checked_at, success, response_ms, status_code, error)`
- `incidents (id, monitor_id, opened_at, resolved_at, acknowledged_at, reason, status)`
- `notifications (id, owner_id, monitor_id, kind, title, message, is_read, created_at)`

### SLA calculation

`sampled_uptime_percent = 100 * successful_HTTP_checks / total_HTTP_checks`

This is an **observed check success rate** rather than an exact percentage of time.
A true production SLA metric should use measured state durations, define scheduled maintenance,
consider data gaps and time-window boundaries, and potentially use independent geographic probes.
The included CSV compares the sampled metric against each monitor's `sla_target`.

### Security notes

- Token auth and Argon2 password hashing; records scoped by `owner_id`.
- Monitor targets limited to HTTP(S), standard ports, and public DNS/IPs; redirects disabled.
- DNS filtering alone **does not fully prevent DNS rebinding**, so a publicly exposed SaaS must also use firewall/egress rules, restricted outbound networks or safe dedicated probing infrastructure.
- Store production secrets in a managed secret store. Enable HTTPS and proper operational protection.
- Public status only includes monitors explicitly marked public, no target URLs or internal incidents.
- This starter does not include rate limiting, password reset, robust RBAC, account email verification or a change log.

### Production upgrade roadmap

1. Move to PostgreSQL + Alembic migrations and index tuning.
2. Move scheduling and probing to dedicated worker pools (Celery/Redis or managed queue), with lease-based locking and retry/backoff.
3. Apply outbound network policies, IP pinning, transport-level SSRF hardening, endpoint ownership verification and quotas.
4. Add consecutive-failure thresholds, notification routing, escalation policies, maintenance windows, idempotent alert delivery and audit logging.
5. Use duration-weighted SLA reporting, SLO error budgets, regional checks and data retention/rollups.
6. Add Prometheus/OpenTelemetry, tracing, dashboards, tests and CI/CD security checks.
