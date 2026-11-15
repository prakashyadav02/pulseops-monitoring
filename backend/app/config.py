import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')


def enabled(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ('true', '1', 'yes', 'on')


DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./pulseops.db')
SECRET_KEY = os.getenv('SECRET_KEY', 'local-development-only-change-me')
ACCESS_TOKEN_MINUTES = int(os.getenv('ACCESS_TOKEN_MINUTES', '1440'))
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
SEED_DEMO = enabled('SEED_DEMO', True)
ENABLE_SCHEDULER = enabled('ENABLE_SCHEDULER', True)
SCHEDULER_POLL_SECONDS = max(5, int(os.getenv('SCHEDULER_POLL_SECONDS', '15')))
try:
    MONITOR_ALLOWED_PORTS = frozenset(
        int(value.strip()) for value in os.getenv('MONITOR_ALLOWED_PORTS', '80,443').split(',')
        if value.strip()
    )
except ValueError as exc:
    raise ValueError('MONITOR_ALLOWED_PORTS must be a comma-separated list of port numbers') from exc
if any(port < 1 or port > 65535 for port in MONITOR_ALLOWED_PORTS):
    raise ValueError('MONITOR_ALLOWED_PORTS values must be between 1 and 65535')
SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', '')
SMTP_STARTTLS = enabled('SMTP_STARTTLS', True)
