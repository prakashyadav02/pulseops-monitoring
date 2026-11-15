import ipaddress
import secrets
import socket
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from sqlalchemy.orm import Session

from . import config
from .database import get_db
from .models import User

password_hash = PasswordHasher()
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bool(password_hash.verify(hashed, password))
    except (VerificationError, VerifyMismatchError):
        return False


def create_token(user_id: int) -> str:
    expiry = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_MINUTES)
    return jwt.encode({'sub': str(user_id), 'exp': expiry}, config.SECRET_KEY, algorithm='HS256')


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated', headers={'WWW-Authenticate': 'Bearer'})
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise unauthorized
    try:
        payload = jwt.decode(credentials.credentials, config.SECRET_KEY, algorithms=['HS256'])
        user_id = int(payload['sub'])
    except (InvalidTokenError, ValueError, KeyError, TypeError):
        raise unauthorized
    user = db.get(User, user_id)
    if not user:
        raise unauthorized
    return user


def new_slug() -> str:
    return secrets.token_urlsafe(9).replace('_', '-').replace('~', '-').lower()


def validate_target_url(url: str):
    """Syntactic SSRF guard; runtime DNS/IP checks happen before every request.

    This is defense in depth for a local starter. A production untrusted URL
    checker must enforce egress ACLs / pin DNS inside its network transport.
    """
    try:
        parsed = urlsplit(url.strip())
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        raise ValueError('Invalid URL or port')
    if parsed.scheme not in ('http', 'https') or not hostname or parsed.username or parsed.password:
        raise ValueError('Enter a valid HTTP(S) URL without credentials')
    if parsed.fragment:
        raise ValueError('Remove the URL fragment (#...)')
    if len(url) > 2048:
        raise ValueError('URL is too long')
    if port is not None and port not in config.MONITOR_ALLOWED_PORTS:
        allowed = ', '.join(str(value) for value in sorted(config.MONITOR_ALLOWED_PORTS))
        raise ValueError(f'Port {port} is not allowed for monitoring. Allowed ports: {allowed}')
    host = hostname.rstrip('.').lower()
    if host in ('localhost', 'localhost.localdomain') or host.endswith(('.localhost', '.local', '.internal', '.test')):
        raise ValueError('Local/private hosts cannot be monitored')
    try:
        ip = ipaddress.ip_address(host.strip('[]'))
    except ValueError:
        if '.' not in host:
            raise ValueError('Enter a publicly resolvable domain')
        return
    if not ip.is_global:
        raise ValueError('Local/private IP addresses are not allowed')


def ensure_public_dns(url: str):
    validate_target_url(url)
    host = urlsplit(url).hostname
    results = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    if not results:
        raise ValueError('DNS returned no addresses')
    for result in results:
        ip = ipaddress.ip_address(result[4][0].split('%')[0])
        if not ip.is_global:
            raise ValueError('Host resolves to a private or reserved IP address')
