from datetime import UTC, datetime, timedelta

import structlog

from app.models.user import User

logger = structlog.get_logger(__name__)

# Paramètres anti-bruteforce
MAX_CONSECUTIVE_LOGIN_FAILURES = 5
ACCOUNT_LOCKOUT_DURATION_MINUTES = 15


class SecurityService:
    """Service managing authentication security rules and account lockout protection."""

    @staticmethod
    def is_account_locked(user: User) -> bool:
        """Check if an account is currently locked due to previous failed attempts."""
        if user.locked_until is None:
            return False

        now = datetime.now(UTC)
        # S'assurer de la comparaison de dates timezone-aware
        locked_until = user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=UTC)

        return now < locked_until

    @staticmethod
    def record_login_failure(user: User) -> None:
        """Increment failed attempts count and lock account if threshold is exceeded."""
        user.failed_login_count += 1
        now = datetime.now(UTC)

        if user.failed_login_count >= MAX_CONSECUTIVE_LOGIN_FAILURES:
            user.locked_until = now + timedelta(minutes=ACCOUNT_LOCKOUT_DURATION_MINUTES)
            logger.warning(
                "Account locked due to consecutive authentication failures",
                user_id=str(user.id),
                email=user.email,
                failed_count=user.failed_login_count,
                locked_until=user.locked_until.isoformat(),
            )
        else:
            logger.info(
                "Recorded failed authentication attempt",
                user_id=str(user.id),
                email=user.email,
                failed_count=user.failed_login_count,
            )

    @staticmethod
    def record_login_success(user: User) -> None:
        """Reset failed login counter, clear lockout and record last login timestamp."""
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)
        logger.info(
            "Recorded successful authentication",
            user_id=str(user.id),
            email=user.email,
        )


security_service = SecurityService()
