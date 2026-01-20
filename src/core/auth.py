"""Authentication service for ChurnPilot."""

import re
from uuid import UUID

import bcrypt

from .database import get_cursor
from .models import User


# Minimum password length
MIN_PASSWORD_LENGTH = 8

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
