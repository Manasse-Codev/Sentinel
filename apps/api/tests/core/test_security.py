import uuid
from datetime import timedelta

import pytest

from app.core.security import (
    InvalidTokenException,
    TokenExpiredException,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)
from app.models.user import User
from app.services.security_service import (
    MAX_CONSECUTIVE_LOGIN_FAILURES,
    security_service,
)


def test_argon2id_password_hashing() -> None:
    """Validate argon2id hashing and verification."""
    password = "SuperSecretPassword123!"
    hashed = get_password_hash(password)

    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_access_token_lifecycle() -> None:
    """Validate creation, claim extraction and decoding of JWT access token."""
    user_id = str(uuid.uuid4())
    email = "analyst@sentinel.local"
    roles = ["analyst", "viewer"]

    token = create_access_token(
        subject=user_id,
        email=email,
        roles=roles,
        expires_delta=timedelta(minutes=10),
    )

    payload = decode_access_token(token)
    assert payload.sub == user_id
    assert payload.email == email
    assert payload.roles == roles
    assert payload.type == "access"


def test_jwt_expired_token_raises_exception() -> None:
    """Validate expired tokens raise TokenExpiredException."""
    token = create_access_token(
        subject=str(uuid.uuid4()),
        email="test@sentinel.local",
        expires_delta=timedelta(seconds=-10),  # In the past
    )

    with pytest.raises(TokenExpiredException):
        decode_access_token(token)


def test_jwt_invalid_token_raises_exception() -> None:
    """Validate malformed tokens raise InvalidTokenException."""
    with pytest.raises(InvalidTokenException):
        decode_access_token("invalid.jwt.token")


def test_refresh_token_generation_and_hash() -> None:
    """Validate refresh token randomness and SHA-256 digest hashing."""
    token1 = generate_refresh_token()
    token2 = generate_refresh_token()

    assert token1 != token2
    assert len(token1) >= 64

    hash1 = hash_refresh_token(token1)
    hash2 = hash_refresh_token(token1)
    assert hash1 == hash2  # deterministic
    assert len(hash1) == 64  # SHA-256 hex string


def test_account_lockout_logic() -> None:
    """Validate account lockout after consecutive failed authentication attempts."""
    user = User(
        id=uuid.uuid4(),
        email="operator@sentinel.local",
        password_hash=get_password_hash("password"),
        is_active=True,
        failed_login_count=0,
        locked_until=None,
    )

    assert security_service.is_account_locked(user) is False

    # Simulate failures below threshold
    for i in range(1, MAX_CONSECUTIVE_LOGIN_FAILURES):
        security_service.record_login_failure(user)
        assert user.failed_login_count == i
        assert security_service.is_account_locked(user) is False

    # Simulate 5th failure -> triggers lockout
    security_service.record_login_failure(user)
    assert user.failed_login_count == MAX_CONSECUTIVE_LOGIN_FAILURES
    assert user.locked_until is not None
    assert security_service.is_account_locked(user) is True

    # Simulate successful login -> resets lockout
    security_service.record_login_success(user)
    assert user.failed_login_count == 0
    assert user.locked_until is None
    assert user.last_login_at is not None
    assert security_service.is_account_locked(user) is False
