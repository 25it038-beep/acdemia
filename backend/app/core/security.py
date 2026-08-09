"""
security.py — JWT and password hashing utilities.

Libraries used:
  - PyJWT  (replaces python-jose which is unmaintained and broken on Python 3.12+)
  - bcrypt (used directly; replaces passlib which is unmaintained and broken with bcrypt>=4.1)
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import bcrypt
from jwt.exceptions import PyJWTError

from app.core.config import settings


# ── Password hashing ──────────────────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


# ── JWT token helpers ─────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a signed JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns None on any error."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except PyJWTError:
        return None


# ── Clerk session token verification ────────────────────────────────────────

_jwks_client = None


def _get_jwks_client() -> "jwt.PyJWKClient":
    """Lazily create (and cache) a JWKS client for the Clerk instance."""
    global _jwks_client
    if _jwks_client is None:
        issuer = settings.CLERK_ISSUER.rstrip("/")
        _jwks_client = jwt.PyJWKClient(f"{issuer}/.well-known/jwks.json", cache_keys=True)
    return _jwks_client


def verify_clerk_token(token: str) -> Optional[dict]:
    """Verify a Clerk session JWT (RS256) against the instance JWKS.

    Returns the token payload on success, None on any error.
    """
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER,
            options={"verify_aud": False},
        )
        return payload
    except PyJWTError:
        return None