# PulseOps

PulseOps is a web app for checking whether websites and HTTP APIs are responding. Add a URL, choose how often it should be checked, and view its status and response time. When a check fails, the app can open an incident and create an alert.

I built this project to learn and bring together a React frontend, a Python API, a database, and a background monitoring task.

## What it does

- Lets users register or sign in and manage their own monitors.
- Checks HTTP and HTTPS URLs on a schedule, or immediately with **Check now**.
- Saves check results, status codes, errors, and response times.
- Tracks incidents when a monitor fails and resolves them after a successful check.
- Shows dashboard and uptime summaries, and exports a sampled SLA report as CSV.
- Provides a public status page for monitors marked public.
- Sends in-app notifications. Email alerts can be enabled with SMTP settings.

The uptime percentage is based on successful checks, not a precise measurement of time online.

## How it is built

- **Frontend:** React, TypeScript, and Vite. The browser app runs at `http://127.0.0.1:5173`.
- **Backend:** Python, FastAPI, and Uvicorn. The API runs at `http://127.0.0.1:8000`.
- **Database:** SQLite by default, accessed through SQLAlchemy. The local database file is created under `backend/` when the API starts. A different database can be configured with `DATABASE_URL`.

The frontend sends requests to the API through Vite's `/api` proxy. FastAPI validates requests, checks the user's access token, and reads or writes records in the database. A scheduler running in the backend looks for monitors that are due, sends HTTP requests to them, and saves the results. Keep the backend running for scheduled checks to happen.

## Run on Windows

### Requirements

- Python 3.11 or newer
- Node.js and npm
- Internet access for installing packages and checking external websites

From PowerShell or the VS Code terminal, change to the project folder and run the setup script once:

```powershell
cd path\to\pulseops-monitoring
.\setup-windows.bat
```

The script creates `.venv`, installs backend and frontend packages, creates local environment files from the examples if they do not exist, and starts the backend and frontend in separate windows.

Open `http://127.0.0.1:5173` in your browser. If demo data is enabled, you can sign in with:

- Email: `demo@pulseops.dev`
- Password: `Demo@12345`

### Start it later

Run `run-windows.bat` from the project folder, or run the services in separate VS Code terminals:

**Terminal 1 — backend** (run from the project root):

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend** (also run from the project root):

```powershell
cd frontend
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. Keep both terminals running; press **Ctrl+C** in each terminal to stop the services.

In PowerShell, `npm` may be blocked by the script execution policy. `npm.cmd` runs the Windows npm command file without changing that policy.

## Run on macOS or Linux

Install Python 3.11+, Node.js, and npm. From the project folder:

```bash
chmod +x setup-unix.sh start-unix.sh
./setup-unix.sh
```

For later starts, run `./start-unix.sh`. Press **Ctrl+C** to stop.

## Useful URLs

- Web app: `http://127.0.0.1:5173`
- Interactive API docs: `http://127.0.0.1:8000/docs`
- API health check: `http://127.0.0.1:8000/health`

## Configure the backend

The setup script copies `backend/.env.example` to `backend/.env`. Edit `backend/.env` to change local settings. For example:

```env
DATABASE_URL=sqlite:///./pulseops.db
SEED_DEMO=true
ENABLE_SCHEDULER=true
SCHEDULER_POLL_SECONDS=15
MONITOR_ALLOWED_PORTS=80,443,4434
```

`MONITOR_ALLOWED_PORTS` is a comma-separated allowlist for ports in monitor URLs. Keep it limited to the ports you need. Restart the backend after changing `.env`.

For optional email notifications, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM` in `backend/.env`, then set the alert email in the app's Settings page.

## API overview

Most `/api` routes require a bearer token. Sign in using `POST /api/auth/login` in the API docs, then use the returned access token to authorize requests.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/auth/register` | Create an account |
| `POST` | `/api/auth/login` | Sign in and receive a token |
| `GET` | `/api/monitors` | List monitors |
| `POST` | `/api/monitors` | Add a monitor |
| `PATCH` | `/api/monitors/{id}` | Update a monitor |
| `DELETE` | `/api/monitors/{id}` | Delete a monitor |
| `POST` | `/api/monitors/{id}/check` | Check a monitor immediately |
| `GET` | `/api/incidents` | View incidents |
| `GET` | `/api/dashboard?range=24h` | Get dashboard statistics |

Use the Swagger page at `http://127.0.0.1:8000/docs` to try these endpoints.

## Notes

- Checks are made by the computer running the backend. It needs network access to the target site.
- Monitor URLs must use HTTP or HTTPS and resolve to a public host. Local and private network addresses are blocked.
- The monitor checks an HTTP response; it does not sign in to websites or verify how a page looks in a browser.
- The scheduler runs inside the API process. This setup is intended for local development and learning, not a production monitoring service.
- Do not commit `.env` files, real credentials, or production secrets. They are excluded by `.gitignore`; keep it that way.

## Project folders

```text
backend/     FastAPI app, database models, monitoring logic, and tests
frontend/    React app and Vite configuration
README.md    Project overview and setup instructions
ARCHITECTURE.md
docker-compose.yml
```
