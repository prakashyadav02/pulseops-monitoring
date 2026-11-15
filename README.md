# PulseOps — FastAPI + React API monitoring platform

**Runnable full-stack portfolio project** with HTTP uptime monitoring, latency history,
automatic incidents, in-app alerts, optional SMTP email alerts, sampled SLA metrics,
CSV export and public status pages. Inspired by the monitoring category, not a copy of PingSLA.

## Quick start (Windows 10/11)

### 1. Install these prerequisites (one time)

- **Python 3.11+** from https://www.python.org/downloads/ . During setup, check **Add python.exe to PATH**.
- **Node.js 22 LTS** from https://nodejs.org/ . It includes npm.
- A modern browser such as Chrome or Edge.
- Internet access **for the first dependency installation**, and to check external endpoints.
- No Docker, Redis or PostgreSQL required for the default setup.

Verify in **Command Prompt**:

```bat
python --version
node --version
npm --version
```


1. Extract `pulseops-monitoring.zip` to a folder such as `C:\Projects\pulseops-monitoring`.
2. Double-click **`setup-windows.bat`**. This creates a virtual environment, installs all Python and npm packages, copies `.env` samples and opens **two** terminal windows.
3. Open **http://127.0.0.1:5173** in your browser.
4. Click **Explore demo workspace** (prefills login) and **Sign in to dashboard**.

Demo login:

| | |
|---|---|
| Email | `demo@pulseops.dev` |
| Password | `Demo@12345` |

The demo user has 4 preconfigured public endpoints and **illustrative historical** measurements. Actual live checks begin when FastAPI starts; the displayed status may change according to real network conditions.

**Next time:** Double-click `run-windows.bat` (no reinstall needed).

Stop the app by closing the two opened terminal windows (or pressing `Ctrl+C` in each).

### Windows — manual terminal commands (if you prefer)

Open **Command Prompt** in the extracted project folder:

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
cd frontend
npm install
cd ..
```

Open **Terminal 1**:

```bat
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open **Terminal 2** (from project root):

```bat
cd frontend
npm run dev
```

Web app: **http://127.0.0.1:5173**  
API docs (Swagger): **http://127.0.0.1:8000/docs**  
Health check: **http://127.0.0.1:8000/health**

## Quick start (macOS / Linux)

Install Python 3.11+, Node 22+ and npm. In Terminal:

```bash
unzip pulseops-monitoring.zip
cd pulseops-monitoring
chmod +x setup-unix.sh start-unix.sh
./setup-unix.sh
```

Later starts: `./start-unix.sh`. Press `Ctrl+C` to stop.

## Alternative: Docker Compose

If Docker Desktop / Docker Engine with Compose is already installed:

```bash
docker compose up --build
```

Open http://127.0.0.1:5173 . SQLite persists in the `pulseops_data` Docker volume.
Note: demo credentials and sample Docker `SECRET_KEY` are **development only**; replace them for deployment.

## Modules included

| Module | Implemented features |
|---|---|
| Authentication | Register, login, signed JWT access tokens, Argon2 password hashing, separate user workspaces |
| Monitor management | Add, edit, delete, pause/resume monitors; expected HTTP status, timeout, interval, SLA target |
| Real monitoring | Server-side scheduled HTTP checks; result/status/latency history; **Check now** button |
| Incident engine | Open incident on first failed check, avoid duplicates, resolve on recovery, acknowledge incidents |
| Alerts | Persistent alert inbox, read/unread notifications; optional SMTP email for down/recovery |
| Analytics | 24-hour, 7-day and 30-day uptime trends, mean response time, status distribution |
| SLA reporting | Per-monitor 30-day sampled uptime vs configurable target, CSV export (1–90 days) |
| Public status | Shareable public page with user-selected monitors only; refreshes every 30 seconds |
| Frontend | React + TypeScript, responsive layout, charts, forms, filters, error/empty states |
| Quality | Backend automated tests, URL guard, API documentation, environment examples, Docker option |

### A five-minute test walkthrough

1. Sign into the demo account and open the **Overview** dashboard.
2. Go to **Monitors → Add monitor**. Name it `Example API`, set URL to `https://example.com`, interval `60 seconds`, SLA target `99.9%`.
3. Click the new monitor and **Check now**. Its state and latency update after the HTTP request.
4. Open the response-time chart; come back after more scheduled checks.
5. To test a controlled failure, create `Broken endpoint` with URL `https://example.com/not-a-real-path` (expected 200). Run **Check now**: the 404 should produce a DOWN state and an OPEN incident.
6. To test the **recovery transition** without changing the URL, edit that monitor’s **Expected HTTP status** from `200` to `404` and click **Check now**. The HTTP 404 is now considered successful, which resolves the incident. (Editing the actual URL instead resets monitoring state and closes the previous incident.)
7. Export **SLA report** from Monitors and open the CSV.
8. Open the **Status page**, copy its link, and view it in a private browser window (no login needed).

The check-based "uptime %" counts successful checks over the selected period. It is **not** a precise contractual duration-based SLA calculation; see `ARCHITECTURE.md` for future improvements.

## Backend configuration

Edit `backend/.env` (automatically created from `.env.example`):

```env
DATABASE_URL=sqlite:///./pulseops.db
SECRET_KEY=replace-with-a-long-random-32-plus-byte-secret
SEED_DEMO=true
ENABLE_SCHEDULER=true
SCHEDULER_POLL_SECONDS=15
```

**Optional SMTP email alerts:**

```env
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-app-password
SMTP_FROM=alerts@your-domain.com
SMTP_STARTTLS=true
```

Then restart the API, open **Settings** in the web app, and set **Alert email** to your destination address. A successful/failed probe creates in-app alerts even without SMTP.

> Security: Never commit `.env`, real credentials, or a real production secret. Demo credentials, the sample secret and auto-seeded history are exclusively for local development. Replace authentication and operational protections before a public launch.

## Backend API endpoints

Interactive Swagger: http://127.0.0.1:8000/docs

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Login and receive JWT |
| `GET` | `/api/auth/me` | Signed-in user |
| `PATCH` | `/api/settings` | Update display name and alert address |
| `GET, POST` | `/api/monitors` | List / add monitors |
| `GET, PATCH, DELETE` | `/api/monitors/{id}` | Detail / edit / delete |
| `POST` | `/api/monitors/{id}/check` | Check immediately |
| `GET` | `/api/monitors/{id}/checks` | Probe history |
| `GET` | `/api/dashboard?range=24h` | Analytics |
| `GET` | `/api/incidents?status=ALL` | Incident list |
| `POST` | `/api/incidents/{id}/acknowledge` | Acknowledge incident |
| `GET` | `/api/notifications` | Notification inbox |
| `POST` | `/api/notifications/read-all` | Mark notifications as read |
| `GET` | `/api/reports/sla.csv?days=30` | Download sampled SLA CSV |
| `GET` | `/api/public/status/{slug}` | Public status (no login) |

## Tests

From the project root (after setup):

**Windows:**

```bat
cd backend
..\.venv\Scripts\python.exe -m pytest -q
```

**macOS/Linux:**

```bash
cd backend
../.venv/bin/python -m pytest -q
```

## Project structure

```text
pulseops-monitoring/
├── setup-windows.bat       # First-time Windows setup + run
├── run-windows.bat         # Subsequent Windows startup
├── setup-unix.sh           # First-time macOS / Linux setup + run
├── start-unix.sh           # Subsequent macOS / Linux startup
├── docker-compose.yml     # Optional Docker environment
├── README.md
├── ARCHITECTURE.md
├── PROJECT_IDEAS.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py         # API endpoints / lifecycle
│   │   ├── config.py       # Configuration
│   │   ├── database.py     # SQLite or PostgreSQL engine
│   │   ├── models.py       # User, Monitor, Check, Incident, Notification
│   │   ├── schemas.py      # Validation / response contracts
│   │   ├── security.py     # JWT, Argon2, URL safety
│   │   ├── services.py     # Monitoring, incidents, SMTP, scheduler
│   │   └── seed.py         # Demo account and sample data
│   └── tests/test_api.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── .env.example
    └── src/
        ├── api.ts, context.tsx, types.ts, utils.ts
        ├── App.tsx, main.tsx, styles.css
        ├── components/
        └── pages/
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognized | Reinstall Python with **Add to PATH**, reopen Command Prompt, check `python --version` |
| `npm` / `node` is not recognized | Install Node.js 22 LTS and reopen terminal |
| `No module named fastapi` | Use the `.venv` Python executable, and re-run `setup-windows.bat` |
| `npm ERR!` / installation failure | Check internet access and proxy settings; retry `cd frontend && npm install` |
| `Failed to fetch` / API unavailable | Make sure the **backend** terminal is open, check http://127.0.0.1:8000/health |
| Port 8000 or 5173 is occupied | Stop the existing process using that port; both startup scripts expect these defaults |
| Monitoring says `DOWN` | Check real external connectivity, DNS, the expected HTTP code, and whether the target blocks bots |
| Localhost/private IP rejected | This is intentional. Use a public endpoint; private targets need a separately protected on-prem agent |
| Demo login not found | Make sure `SEED_DEMO=true` in backend `.env`, then restart API |
| No email delivered | Set SMTP variables **and** Settings → Alert email; review backend log messages |
| Database schema error after modifying code | For a **fresh demo only**, stop API and delete `backend/pulseops.db`; startup recreates it. This permanently erases local data. For real data, use Alembic migrations. |

## Scope and deployment safety

This is a **working local development / portfolio starter**, not a production monitoring SaaS. The scheduler runs inside a single API process and should not be used with multiple server workers. Production work should include a dedicated distributed scheduler with task locking, durable queues, database migrations, TLS, endpoint rate limits, retries/debounce policies, secret management, restricted egress to prevent DNS rebinding / SSRF, audit logging, data retention, privacy/security review, and proper duration-weighted SLA / multi-region checks. See `ARCHITECTURE.md`.
