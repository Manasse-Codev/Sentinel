import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import structlog
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError, VerifyMismatchError
from jwt.exceptions import InvalidTokenError, PyJWTError

from app.core.config import settings
from app.schemas.token import TokenPayload

logger = structlog.get_logger(__name__)

# Argon2id password hasher configuration (OWASP recommended parameters)
_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    type=Type.ID,  # argon2id strictly
)


class SecurityException(Exception):
    """Base domain security exception."""

    pass


class TokenExpiredException(SecurityException):
    """Exception raised when a JWT token has expired."""

    pass


class InvalidTokenException(SecurityException):
    """Exception raised when a JWT token is malformed, has invalid claims or wrong signature."""

    pass


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using argon2id."""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an argon2id hash."""
    try:
        return _password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError):
        return False
    except Exception as e:
        logger.error("Unexpected error during password verification", error=str(e))
        return False


def generate_refresh_token() -> str:
    """Generate a cryptographically secure random opaque string for refresh token."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(refresh_token: str) -> str:
    """Compute SHA-256 digest of the opaque refresh token for safe storage."""
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: str,
    email: str,
    roles: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    claims: dict[str, Any] = {
        "sub": subject,
        "email": email,
        "roles": roles or [],
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access",
    }

    token = jwt.encode(
        claims,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a signed JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
        )
        if payload.get("type") != "access":
            raise InvalidTokenException("Invalid token type")

        return TokenPayload(
            sub=str(payload["sub"]),
            email=str(payload.get("email", "")),
            roles=list(payload.get("roles", [])),
            exp=int(payload["exp"]),
            iat=int(payload["iat"]),
            type=str(payload.get("type", "access")),
        )
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredException("Access token has expired") from e
    except (InvalidTokenError, PyJWTError) as e:
        raise InvalidTokenException("Could not validate token credentials") from e
