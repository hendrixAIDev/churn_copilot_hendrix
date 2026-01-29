"""Authentication service for ChurnPilot."""

import re
import secrets
from datetime import datetime, timedelta
from uuid import UUID

import bcrypt

from .database import get_cursor
from .models import User


# Minimum password length
MIN_PASSWORD_LENGTH = 8

# Session configuration
SESSION_TOKEN_BYTES = 32  # 32 bytes = 64 hex characters
SESSION_EXPIRY_HOURS = 24  # Sessions expire after 24 hours of inactivity

# Email regex pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password.

    Returns:
        Hashed password string.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash.

    Args:
        password: Plain text password to verify.
        password_hash: Stored bcrypt hash.

    Returns:
        True if password matches.
    """
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """Validate email format.

    Args:
        email: Email address to validate.

    Returns:
        True if valid format.
    """
    if not email:
        return False
    return bool(EMAIL_PATTERN.match(email))


def validate_password(password: str) -> bool:
    """Validate password meets requirements.

    Args:
        password: Password to validate.

    Returns:
        True if meets requirements.
    """
    if not password:
        return False
    return len(password) >= MIN_PASSWORD_LENGTH


class AuthService:
    """Authentication service for user management."""

    def register(self, email: str, password: str) -> User:
        """Register a new user.

        Args:
            email: User's email address.
            password: User's password (plain text).

        Returns:
            Created User object.

        Raises:
            ValueError: If email/password invalid or email already exists.
        """
        # Validate inputs
        email = email.lower().strip()

        if not validate_email(email):
            raise ValueError("Invalid email format")

        if not validate_password(password):
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

        # Hash password
        password_hash = hash_password(password)

        # Insert user
        with get_cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO users (email, password_hash)
                    VALUES (%s, %s)
                    RETURNING id, email, created_at, updated_at
                    """,
                    (email, password_hash)
                )
                row = cursor.fetchone()
                return User(
                    id=row["id"],
                    email=row["email"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            except Exception as e:
                if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                    raise ValueError("Email already registered")
                raise

    def login(self, email: str, password: str) -> User | None:
        """Authenticate a user.

        Args:
            email: User's email address.
            password: User's password (plain text).

        Returns:
            User object if credentials valid, None otherwise.
        """
        email = email.lower().strip()

        with get_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT id, email, password_hash, created_at, updated_at
                FROM users
                WHERE email = %s
                """,
                (email,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            if not verify_password(password, row["password_hash"]):
                return None

            return User(
                id=row["id"],
                email=row["email"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def get_user(self, user_id: UUID) -> User | None:
        """Get user by ID.

        Args:
            user_id: User's UUID.

        Returns:
            User object if found, None otherwise.
        """
        with get_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT id, email, created_at, updated_at
                FROM users
                WHERE id = %s
                """,
                (str(user_id),)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return User(
                id=row["id"],
                email=row["email"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def change_password(
        self,
        user_id: UUID,
        old_password: str,
        new_password: str
    ) -> bool:
        """Change user's password.

        Args:
            user_id: User's UUID.
            old_password: Current password.
            new_password: New password.

        Returns:
            True if password changed successfully.

        Raises:
            ValueError: If new password doesn't meet requirements.
        """
        if not validate_password(new_password):
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")

        # Verify old password
        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT password_hash FROM users WHERE id = %s",
                (str(user_id),)
            )
            row = cursor.fetchone()

            if not row or not verify_password(old_password, row["password_hash"]):
                return False

        # Update password
        new_hash = hash_password(new_password)

        with get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (new_hash, str(user_id))
            )
            return cursor.rowcount > 0

    def delete_user(self, user_id: UUID) -> bool:
        """Delete a user and all their data.

        Args:
            user_id: User's UUID.

        Returns:
            True if user deleted.
        """
        with get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM users WHERE id = %s",
                (str(user_id),)
            )
            return cursor.rowcount > 0

    def create_session(self, user_id: UUID) -> str:
        """Create a new session for a user.

        Creates a secure session token stored in database with 24hr expiry.
        Old sessions for this user are cleaned up.

        Args:
            user_id: User's UUID.

        Returns:
            Session token string (64 hex characters).
        """
        # Generate secure random token
        token = secrets.token_hex(SESSION_TOKEN_BYTES)
        expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)

        with get_cursor() as cursor:
            # Clean up old sessions for this user (keep max 5 active sessions)
            cursor.execute(
                """
                DELETE FROM sessions
                WHERE user_id = %s
                AND id NOT IN (
                    SELECT id FROM sessions
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 4
                )
                """,
                (str(user_id), str(user_id))
            )

            # Also clean up expired sessions globally
            cursor.execute(
                "DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP"
            )

            # Create new session
            cursor.execute(
                """
                INSERT INTO sessions (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                RETURNING token
                """,
                (str(user_id), token, expires_at)
            )

        return token

    def validate_session(self, token: str) -> User | None:
        """Validate a session token and return the user if valid.

        Also refreshes the session expiry (sliding window).

        Args:
            token: Session token to validate.

        Returns:
            User object if session is valid and not expired, None otherwise.
        """
        if not token or len(token) != SESSION_TOKEN_BYTES * 2:
            return None

        with get_cursor() as cursor:
            # Get session and user in one query
            cursor.execute(
                """
                SELECT u.id, u.email, u.created_at, u.updated_at, s.expires_at
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.token = %s
                """,
                (token,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            # Check if expired
            if row["expires_at"] < datetime.utcnow():
                # Clean up expired session
                cursor.execute(
                    "DELETE FROM sessions WHERE token = %s",
                    (token,)
                )
                return None

            # Refresh session expiry (sliding window - extends 24hr from now)
            new_expiry = datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)
            cursor.execute(
                """
                UPDATE sessions
                SET expires_at = %s
                WHERE token = %s
                """,
                (new_expiry, token)
            )

            return User(
                id=row["id"],
                email=row["email"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def delete_session(self, token: str) -> bool:
        """Delete a session (logout).

        Args:
            token: Session token to delete.

        Returns:
            True if session was deleted.
        """
        with get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM sessions WHERE token = %s",
                (token,)
            )
            return cursor.rowcount > 0

    def delete_all_sessions(self, user_id: UUID) -> int:
        """Delete all sessions for a user (logout from all devices).

        Args:
            user_id: User's UUID.

        Returns:
            Number of sessions deleted.
        """
        with get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM sessions WHERE user_id = %s",
                (str(user_id),)
            )
            return cursor.rowcount
