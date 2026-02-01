# User Authentication Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add PostgreSQL database with user authentication to ChurnPilot, replacing localStorage.

**Architecture:** PostgreSQL for data persistence, bcrypt for password hashing, Streamlit session_state for login sessions. Storage adapter pattern keeps existing app code mostly unchanged.

**Tech Stack:** PostgreSQL, psycopg2-binary, bcrypt, python-dotenv

---

## Task 1: Add Dependencies

**Files:**
- Modify: `requirements.txt`
- Create: `.env.example`

**Step 1: Update requirements.txt**

Add these lines to `requirements.txt`:

```
# Database
psycopg2-binary>=2.9.0
bcrypt>=4.0.0
```

**Step 2: Create .env.example**

Create `.env.example`:

```bash
# Database connection (required)
# Get free PostgreSQL from: neon.tech, supabase.com, or railway.app
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Example for local development:
# DATABASE_URL=postgresql://localhost:5432/churnpilot
```

**Step 3: Commit**

```bash
git add requirements.txt .env.example
git commit -m "chore: add database dependencies"
```

---

## Task 2: Create Database Module

**Files:**
- Create: `src/core/database.py`
- Create: `tests/test_database.py`

**Step 1: Write the failing test**

Create `tests/test_database.py`:

```python
"""Tests for database module."""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestDatabaseConnection:
    """Test database connection handling."""

    def test_get_database_url_from_env(self):
        """Should read DATABASE_URL from environment."""
        from src.core.database import get_database_url

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/testdb"}):
            url = get_database_url()
            assert url == "postgresql://test:test@localhost/testdb"

    def test_get_database_url_missing_raises(self):
        """Should raise if DATABASE_URL not set."""
        from src.core.database import get_database_url

        with patch.dict(os.environ, {}, clear=True):
            # Remove DATABASE_URL if it exists
            os.environ.pop("DATABASE_URL", None)
            with pytest.raises(ValueError, match="DATABASE_URL"):
                get_database_url()


class TestDatabaseSchema:
    """Test schema creation."""

    def test_get_schema_sql_returns_string(self):
        """Should return SQL schema as string."""
        from src.core.database import get_schema_sql

        sql = get_schema_sql()
        assert isinstance(sql, str)
        assert "CREATE TABLE users" in sql
        assert "CREATE TABLE cards" in sql
        assert "CREATE TABLE user_preferences" in sql
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_database.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.core.database'"

**Step 3: Write minimal implementation**

Create `src/core/database.py`:

```python
"""Database connection and schema management for ChurnPilot."""

import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.extras import RealDictCursor


def get_database_url() -> str:
    """Get database URL from environment.

    Returns:
        PostgreSQL connection URL.

    Raises:
        ValueError: If DATABASE_URL is not set.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Set it to your PostgreSQL connection string."
        )
    return url


def get_schema_sql() -> str:
    """Get SQL schema for all tables.

    Returns:
        SQL string to create all tables.
    """
    return """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

    -- User preferences
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        sort_by VARCHAR(50) DEFAULT 'date_added',
        sort_descending BOOLEAN DEFAULT TRUE,
        group_by_issuer BOOLEAN DEFAULT FALSE,
        auto_enrich_enabled BOOLEAN DEFAULT TRUE,
        enrichment_min_confidence FLOAT DEFAULT 0.7,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Cards
    CREATE TABLE IF NOT EXISTS cards (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        nickname VARCHAR(255),
        issuer VARCHAR(100) NOT NULL,
        annual_fee INTEGER DEFAULT 0,
        opened_date DATE,
        annual_fee_date DATE,
        closed_date DATE,
        is_business BOOLEAN DEFAULT FALSE,
        notes TEXT,
        raw_text TEXT,
        template_id VARCHAR(100),
        benefits_reminder_snoozed_until DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_cards_user_id ON cards(user_id);
    CREATE INDEX IF NOT EXISTS idx_cards_issuer ON cards(issuer);

    -- Signup bonuses (one per card)
    CREATE TABLE IF NOT EXISTS signup_bonuses (
        card_id UUID PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE,
        points_or_cash VARCHAR(100) NOT NULL,
        spend_requirement FLOAT NOT NULL,
        time_period_days INTEGER NOT NULL,
        deadline DATE,
        spend_progress FLOAT DEFAULT 0,
        achieved BOOLEAN DEFAULT FALSE
    );

    -- Card credits/perks
    CREATE TABLE IF NOT EXISTS card_credits (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        amount FLOAT NOT NULL,
        frequency VARCHAR(50) DEFAULT 'monthly',
        notes TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_card_credits_card_id ON card_credits(card_id);

    -- Credit usage tracking
    CREATE TABLE IF NOT EXISTS credit_usage (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
        credit_name VARCHAR(255) NOT NULL,
        last_used_period VARCHAR(20),
        reminder_snoozed_until DATE,
        UNIQUE(card_id, credit_name)
    );
    CREATE INDEX IF NOT EXISTS idx_credit_usage_card_id ON credit_usage(card_id);

    -- Retention offers
    CREATE TABLE IF NOT EXISTS retention_offers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
        date_called DATE NOT NULL,
        offer_details TEXT NOT NULL,
        accepted BOOLEAN NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_retention_offers_card_id ON retention_offers(card_id);

    -- Product changes
    CREATE TABLE IF NOT EXISTS product_changes (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
        date_changed DATE NOT NULL,
        from_product VARCHAR(255) NOT NULL,
        to_product VARCHAR(255) NOT NULL,
        reason TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_product_changes_card_id ON product_changes(card_id);
    """


@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Get a database connection.

    Yields:
        Database connection (auto-closed on exit).
    """
    conn = psycopg2.connect(get_database_url())
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_cursor(commit: bool = True) -> Generator[RealDictCursor, None, None]:
    """Get a database cursor with dict results.

    Args:
        commit: Whether to commit on successful exit.

    Yields:
        Database cursor (auto-closed on exit).
    """
    with get_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()


def init_database() -> None:
    """Initialize database schema.

    Creates all tables if they don't exist.
    """
    with get_cursor() as cursor:
        cursor.execute(get_schema_sql())


def check_connection() -> bool:
    """Check if database connection works.

    Returns:
        True if connection successful.
    """
    try:
        with get_cursor(commit=False) as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception:
        return False
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_database.py::TestDatabaseConnection -v
python -m pytest tests/test_database.py::TestDatabaseSchema -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/core/database.py tests/test_database.py
git commit -m "feat: add database module with schema"
```

---

## Task 3: Create Database Init Script

**Files:**
- Create: `scripts/init_db.py`

**Step 1: Create the script**

Create `scripts/init_db.py`:

```python
#!/usr/bin/env python3
"""Initialize the ChurnPilot database.

Usage:
    python scripts/init_db.py

Requires DATABASE_URL environment variable to be set.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

from src.core.database import init_database, check_connection, get_database_url


def main():
    """Initialize the database."""
    print("ChurnPilot Database Initialization")
    print("=" * 40)

    # Check DATABASE_URL is set
    try:
        url = get_database_url()
        # Hide password in output
        safe_url = url.split("@")[-1] if "@" in url else url
        print(f"Database: ...@{safe_url}")
    except ValueError as e:
        print(f"ERROR: {e}")
        print("\nSet DATABASE_URL in your .env file or environment.")
        sys.exit(1)

    # Test connection
    print("\nTesting connection...")
    if not check_connection():
        print("ERROR: Could not connect to database.")
        print("Check your DATABASE_URL and ensure the database server is running.")
        sys.exit(1)
    print("Connection successful!")

    # Initialize schema
    print("\nCreating tables...")
    try:
        init_database()
        print("Schema initialized successfully!")
    except Exception as e:
        print(f"ERROR: Failed to create tables: {e}")
        sys.exit(1)

    print("\n" + "=" * 40)
    print("Database ready!")


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add scripts/init_db.py
git commit -m "feat: add database initialization script"
```

---

## Task 4: Create User Model

**Files:**
- Modify: `src/core/models.py`
- Create: `tests/test_user_model.py`

**Step 1: Write the failing test**

Create `tests/test_user_model.py`:

```python
"""Tests for User model."""

import pytest
from uuid import UUID
from datetime import datetime


class TestUserModel:
    """Test User model."""

    def test_user_model_creation(self):
        """Should create user with required fields."""
        from src.core.models import User

        user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
        )

        assert user.email == "test@example.com"
        assert isinstance(user.id, UUID)

    def test_user_email_normalized_lowercase(self):
        """Should normalize email to lowercase."""
        from src.core.models import User

        user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="Test@EXAMPLE.com",
        )

        assert user.email == "test@example.com"

    def test_user_optional_timestamps(self):
        """Should have optional timestamps."""
        from src.core.models import User

        user = User(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            created_at=datetime.now(),
        )

        assert user.created_at is not None
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_user_model.py -v
```

Expected: FAIL with "cannot import name 'User'"

**Step 3: Add User model to models.py**

Add to `src/core/models.py` (after imports, before Credit class):

```python
from uuid import UUID


class User(BaseModel):
    """A user account."""

    id: UUID = Field(..., description="Unique identifier")
    email: str = Field(..., description="User email (unique, lowercase)")
    created_at: datetime | None = Field(default=None, description="Account creation time")
    updated_at: datetime | None = Field(default=None, description="Last update time")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip() if v else v
```

Also add to imports at top:

```python
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_user_model.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/core/models.py tests/test_user_model.py
git commit -m "feat: add User model"
```

---

## Task 5: Create Auth Service

**Files:**
- Create: `src/core/auth.py`
- Create: `tests/test_auth.py`

**Step 1: Write the failing test**

Create `tests/test_auth.py`:

```python
"""Tests for authentication service."""

import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password_returns_string(self):
        """Should hash password and return string."""
        from src.core.auth import hash_password

        hashed = hash_password("mysecretpassword")

        assert isinstance(hashed, str)
        assert hashed != "mysecretpassword"
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        """Should verify correct password."""
        from src.core.auth import hash_password, verify_password

        password = "mysecretpassword"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Should reject incorrect password."""
        from src.core.auth import hash_password, verify_password

        hashed = hash_password("correctpassword")

        assert verify_password("wrongpassword", hashed) is False


class TestEmailValidation:
    """Test email validation."""

    def test_valid_email(self):
        """Should accept valid email."""
        from src.core.auth import validate_email

        assert validate_email("user@example.com") is True
        assert validate_email("user.name@domain.co.uk") is True

    def test_invalid_email(self):
        """Should reject invalid email."""
        from src.core.auth import validate_email

        assert validate_email("not-an-email") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("") is False


class TestPasswordValidation:
    """Test password validation."""

    def test_valid_password(self):
        """Should accept password >= 8 chars."""
        from src.core.auth import validate_password

        assert validate_password("12345678") is True
        assert validate_password("longpassword123") is True

    def test_invalid_password(self):
        """Should reject password < 8 chars."""
        from src.core.auth import validate_password

        assert validate_password("1234567") is False
        assert validate_password("short") is False
        assert validate_password("") is False
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_auth.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.core.auth'"

**Step 3: Write implementation**

Create `src/core/auth.py`:

```python
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
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_auth.py -v
```

Expected: PASS (for validation/hashing tests - DB tests need actual DB)

**Step 5: Commit**

```bash
git add src/core/auth.py tests/test_auth.py
git commit -m "feat: add authentication service"
```

---

## Task 6: Create Database Storage

**Files:**
- Create: `src/core/db_storage.py`
- Create: `tests/test_db_storage.py`

**Step 1: Write the failing test**

Create `tests/test_db_storage.py`:

```python
"""Tests for database storage."""

import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID
from datetime import date


class TestDatabaseStorageInterface:
    """Test DatabaseStorage has correct interface."""

    def test_has_get_all_cards_method(self):
        """Should have get_all_cards method."""
        from src.core.db_storage import DatabaseStorage

        assert hasattr(DatabaseStorage, "get_all_cards")

    def test_has_save_card_method(self):
        """Should have save_card method."""
        from src.core.db_storage import DatabaseStorage

        assert hasattr(DatabaseStorage, "save_card")

    def test_has_delete_card_method(self):
        """Should have delete_card method."""
        from src.core.db_storage import DatabaseStorage

        assert hasattr(DatabaseStorage, "delete_card")

    def test_has_get_preferences_method(self):
        """Should have get_preferences method."""
        from src.core.db_storage import DatabaseStorage

        assert hasattr(DatabaseStorage, "get_preferences")

    def test_has_save_preferences_method(self):
        """Should have save_preferences method."""
        from src.core.db_storage import DatabaseStorage

        assert hasattr(DatabaseStorage, "save_preferences")
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_db_storage.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write implementation**

Create `src/core/db_storage.py`:

```python
"""Database storage for ChurnPilot.

Provides the same interface as WebStorage but backed by PostgreSQL.
All operations are scoped to a specific user_id.
"""

from datetime import date, datetime
from uuid import UUID
import uuid as uuid_module

from .database import get_cursor
from .models import (
    Card, CardData, SignupBonus, Credit,
    CreditUsage, RetentionOffer, ProductChange
)
from .preferences import UserPreferences
from .library import CardTemplate
from .normalize import normalize_issuer, match_to_library_template


class DatabaseStorage:
    """PostgreSQL-backed storage for a single user."""

    def __init__(self, user_id: UUID):
        """Initialize storage for a user.

        Args:
            user_id: The user's UUID (all operations scoped to this user).
        """
        self.user_id = user_id

    # ==================== CARDS ====================

    def get_all_cards(self) -> list[Card]:
        """Get all cards for the user.

        Returns:
            List of Card objects.
        """
        with get_cursor(commit=False) as cursor:
            # Get cards
            cursor.execute(
                """
                SELECT * FROM cards WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (str(self.user_id),)
            )
            card_rows = cursor.fetchall()

            cards = []
            for row in card_rows:
                card_id = row["id"]

                # Get signup bonus
                cursor.execute(
                    "SELECT * FROM signup_bonuses WHERE card_id = %s",
                    (str(card_id),)
                )
                sub_row = cursor.fetchone()
                signup_bonus = None
                sub_progress = None
                sub_achieved = False
                if sub_row:
                    signup_bonus = SignupBonus(
                        points_or_cash=sub_row["points_or_cash"],
                        spend_requirement=sub_row["spend_requirement"],
                        time_period_days=sub_row["time_period_days"],
                        deadline=sub_row["deadline"],
                    )
                    sub_progress = sub_row["spend_progress"]
                    sub_achieved = sub_row["achieved"]

                # Get credits
                cursor.execute(
                    "SELECT * FROM card_credits WHERE card_id = %s",
                    (str(card_id),)
                )
                credit_rows = cursor.fetchall()
                credits = [
                    Credit(
                        name=r["name"],
                        amount=r["amount"],
                        frequency=r["frequency"],
                        notes=r["notes"],
                    )
                    for r in credit_rows
                ]

                # Get credit usage
                cursor.execute(
                    "SELECT * FROM credit_usage WHERE card_id = %s",
                    (str(card_id),)
                )
                usage_rows = cursor.fetchall()
                credit_usage = {
                    r["credit_name"]: CreditUsage(
                        last_used_period=r["last_used_period"],
                        reminder_snoozed_until=r["reminder_snoozed_until"],
                    )
                    for r in usage_rows
                }

                # Get retention offers
                cursor.execute(
                    "SELECT * FROM retention_offers WHERE card_id = %s ORDER BY date_called DESC",
                    (str(card_id),)
                )
                retention_rows = cursor.fetchall()
                retention_offers = [
                    RetentionOffer(
                        date_called=r["date_called"],
                        offer_details=r["offer_details"],
                        accepted=r["accepted"],
                        notes=r["notes"],
                    )
                    for r in retention_rows
                ]

                # Get product changes
                cursor.execute(
                    "SELECT * FROM product_changes WHERE card_id = %s ORDER BY date_changed DESC",
                    (str(card_id),)
                )
                change_rows = cursor.fetchall()
                product_changes = [
                    ProductChange(
                        date_changed=r["date_changed"],
                        from_product=r["from_product"],
                        to_product=r["to_product"],
                        reason=r["reason"],
                        notes=r["notes"],
                    )
                    for r in change_rows
                ]

                # Build card
                card = Card(
                    id=str(card_id),
                    name=row["name"],
                    nickname=row["nickname"],
                    issuer=row["issuer"],
                    annual_fee=row["annual_fee"],
                    signup_bonus=signup_bonus,
                    sub_spend_progress=sub_progress,
                    sub_achieved=sub_achieved,
                    credits=credits,
                    opened_date=row["opened_date"],
                    annual_fee_date=row["annual_fee_date"],
                    closed_date=row["closed_date"],
                    is_business=row["is_business"],
                    notes=row["notes"],
                    raw_text=row["raw_text"],
                    template_id=row["template_id"],
                    created_at=row["created_at"],
                    credit_usage=credit_usage,
                    benefits_reminder_snoozed_until=row["benefits_reminder_snoozed_until"],
                    retention_offers=retention_offers,
                    product_change_history=product_changes,
                )
                cards.append(card)

            return cards

    def get_card(self, card_id: str) -> Card | None:
        """Get a single card by ID.

        Args:
            card_id: The card's UUID string.

        Returns:
            Card if found, None otherwise.
        """
        cards = self.get_all_cards()
        for card in cards:
            if card.id == card_id:
                return card
        return None

    def save_card(self, card: Card) -> Card:
        """Save a card (insert or update).

        Args:
            card: Card to save.

        Returns:
            Saved card.
        """
        with get_cursor() as cursor:
            # Check if card exists
            cursor.execute(
                "SELECT id FROM cards WHERE id = %s AND user_id = %s",
                (card.id, str(self.user_id))
            )
            exists = cursor.fetchone() is not None

            if exists:
                # Update
                cursor.execute(
                    """
                    UPDATE cards SET
                        name = %s, nickname = %s, issuer = %s, annual_fee = %s,
                        opened_date = %s, annual_fee_date = %s, closed_date = %s,
                        is_business = %s, notes = %s, raw_text = %s, template_id = %s,
                        benefits_reminder_snoozed_until = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    """,
                    (
                        card.name, card.nickname, card.issuer, card.annual_fee,
                        card.opened_date, card.annual_fee_date, card.closed_date,
                        card.is_business, card.notes, card.raw_text, card.template_id,
                        card.benefits_reminder_snoozed_until, card.id, str(self.user_id)
                    )
                )
            else:
                # Insert
                cursor.execute(
                    """
                    INSERT INTO cards (
                        id, user_id, name, nickname, issuer, annual_fee,
                        opened_date, annual_fee_date, closed_date, is_business,
                        notes, raw_text, template_id, benefits_reminder_snoozed_until, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        card.id, str(self.user_id), card.name, card.nickname,
                        card.issuer, card.annual_fee, card.opened_date,
                        card.annual_fee_date, card.closed_date, card.is_business,
                        card.notes, card.raw_text, card.template_id,
                        card.benefits_reminder_snoozed_until,
                        card.created_at or datetime.now()
                    )
                )

            # Save signup bonus
            cursor.execute("DELETE FROM signup_bonuses WHERE card_id = %s", (card.id,))
            if card.signup_bonus:
                cursor.execute(
                    """
                    INSERT INTO signup_bonuses (
                        card_id, points_or_cash, spend_requirement, time_period_days,
                        deadline, spend_progress, achieved
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        card.id, card.signup_bonus.points_or_cash,
                        card.signup_bonus.spend_requirement,
                        card.signup_bonus.time_period_days,
                        card.signup_bonus.deadline,
                        card.sub_spend_progress or 0,
                        card.sub_achieved or False
                    )
                )

            # Save credits
            cursor.execute("DELETE FROM card_credits WHERE card_id = %s", (card.id,))
            for credit in card.credits:
                cursor.execute(
                    """
                    INSERT INTO card_credits (card_id, name, amount, frequency, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (card.id, credit.name, credit.amount, credit.frequency, credit.notes)
                )

            # Save credit usage
            cursor.execute("DELETE FROM credit_usage WHERE card_id = %s", (card.id,))
            for credit_name, usage in card.credit_usage.items():
                cursor.execute(
                    """
                    INSERT INTO credit_usage (card_id, credit_name, last_used_period, reminder_snoozed_until)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (card.id, credit_name, usage.last_used_period, usage.reminder_snoozed_until)
                )

            # Save retention offers
            cursor.execute("DELETE FROM retention_offers WHERE card_id = %s", (card.id,))
            for offer in card.retention_offers:
                cursor.execute(
                    """
                    INSERT INTO retention_offers (card_id, date_called, offer_details, accepted, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (card.id, offer.date_called, offer.offer_details, offer.accepted, offer.notes)
                )

            # Save product changes
            cursor.execute("DELETE FROM product_changes WHERE card_id = %s", (card.id,))
            for change in card.product_change_history:
                cursor.execute(
                    """
                    INSERT INTO product_changes (card_id, date_changed, from_product, to_product, reason, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (card.id, change.date_changed, change.from_product, change.to_product, change.reason, change.notes)
                )

        return card

    def add_card(
        self,
        card_data: CardData,
        opened_date: date | None = None,
        raw_text: str | None = None,
    ) -> Card:
        """Add a card from extracted data.

        Args:
            card_data: Extracted card data.
            opened_date: When card was opened.
            raw_text: Original text used for extraction.

        Returns:
            Created Card.
        """
        card = Card(
            id=str(uuid_module.uuid4()),
            name=card_data.name,
            issuer=normalize_issuer(card_data.issuer),
            annual_fee=card_data.annual_fee,
            signup_bonus=card_data.signup_bonus,
            credits=card_data.credits,
            opened_date=opened_date,
            raw_text=raw_text,
            template_id=match_to_library_template(
                card_data.name,
                normalize_issuer(card_data.issuer)
            ),
            created_at=datetime.now(),
        )
        return self.save_card(card)

    def add_card_from_template(
        self,
        template: CardTemplate,
        nickname: str | None = None,
        opened_date: date | None = None,
        signup_bonus: SignupBonus | None = None,
    ) -> Card:
        """Add a card from a library template.

        Args:
            template: Library template.
            nickname: User nickname for card.
            opened_date: When card was opened.
            signup_bonus: SUB details.

        Returns:
            Created Card.
        """
        card = Card(
            id=str(uuid_module.uuid4()),
            name=template.name,
            nickname=nickname,
            issuer=template.issuer,
            annual_fee=template.annual_fee,
            signup_bonus=signup_bonus,
            credits=template.credits,
            opened_date=opened_date,
            template_id=template.id,
            created_at=datetime.now(),
        )
        return self.save_card(card)

    def update_card(self, card_id: str, updates: dict) -> Card | None:
        """Update a card by ID.

        Args:
            card_id: Card's UUID string.
            updates: Fields to update.

        Returns:
            Updated Card or None if not found.
        """
        card = self.get_card(card_id)
        if not card:
            return None

        # Apply updates
        card_dict = card.model_dump()
        card_dict.update(updates)
        updated_card = Card.model_validate(card_dict)

        return self.save_card(updated_card)

    def delete_card(self, card_id: str) -> bool:
        """Delete a card by ID.

        Args:
            card_id: Card's UUID string.

        Returns:
            True if deleted.
        """
        with get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM cards WHERE id = %s AND user_id = %s",
                (card_id, str(self.user_id))
            )
            return cursor.rowcount > 0

    # ==================== PREFERENCES ====================

    def get_preferences(self) -> UserPreferences:
        """Get user preferences.

        Returns:
            UserPreferences (defaults if not set).
        """
        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM user_preferences WHERE user_id = %s",
                (str(self.user_id),)
            )
            row = cursor.fetchone()

            if not row:
                return UserPreferences()

            return UserPreferences(
                sort_by=row["sort_by"],
                sort_descending=row["sort_descending"],
                group_by_issuer=row["group_by_issuer"],
                auto_enrich_enabled=row["auto_enrich_enabled"],
                enrichment_min_confidence=row["enrichment_min_confidence"],
            )

    def save_preferences(self, prefs: UserPreferences) -> None:
        """Save user preferences.

        Args:
            prefs: Preferences to save.
        """
        with get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_preferences (
                    user_id, sort_by, sort_descending, group_by_issuer,
                    auto_enrich_enabled, enrichment_min_confidence
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    sort_by = EXCLUDED.sort_by,
                    sort_descending = EXCLUDED.sort_descending,
                    group_by_issuer = EXCLUDED.group_by_issuer,
                    auto_enrich_enabled = EXCLUDED.auto_enrich_enabled,
                    enrichment_min_confidence = EXCLUDED.enrichment_min_confidence,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    str(self.user_id), prefs.sort_by, prefs.sort_descending,
                    prefs.group_by_issuer, prefs.auto_enrich_enabled,
                    prefs.enrichment_min_confidence
                )
            )

    def update_preference(self, key: str, value) -> UserPreferences:
        """Update a single preference.

        Args:
            key: Preference key.
            value: New value.

        Returns:
            Updated preferences.
        """
        prefs = self.get_preferences()
        if hasattr(prefs, key):
            setattr(prefs, key, value)
            self.save_preferences(prefs)
        return prefs

    # ==================== EXPORT/IMPORT ====================

    def export_data(self) -> str:
        """Export all cards as JSON.

        Returns:
            JSON string of cards.
        """
        import json
        cards = self.get_all_cards()
        return json.dumps([c.model_dump() for c in cards], indent=2, default=str)

    def import_data(self, json_data: str) -> int:
        """Import cards from JSON.

        Args:
            json_data: JSON string of cards.

        Returns:
            Number of cards imported.
        """
        import json
        data = json.loads(json_data)
        if not isinstance(data, list):
            raise ValueError("Must be a JSON array")

        count = 0
        for item in data:
            try:
                card = Card.model_validate(item)
                # Generate new ID to avoid conflicts
                card.id = str(uuid_module.uuid4())
                self.save_card(card)
                count += 1
            except Exception:
                pass  # Skip invalid cards

        return count
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_db_storage.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/core/db_storage.py tests/test_db_storage.py
git commit -m "feat: add database storage layer"
```

---

## Task 7: Add Login/Register UI

**Files:**
- Modify: `src/ui/app.py`

**Step 1: Add auth imports and helper functions at top of app.py**

After existing imports, add:

```python
from src.core.auth import AuthService, validate_email, validate_password, MIN_PASSWORD_LENGTH
from src.core.db_storage import DatabaseStorage
from src.core.database import check_connection
```

**Step 2: Add login/register page function**

Add this function before the main app logic:

```python
def show_auth_page():
    """Show login/register page.

    Returns:
        True if user is authenticated, False otherwise.
    """
    st.title("ChurnPilot")
    st.markdown("AI-powered credit card churning management")

    # Check database connection
    if not check_connection():
        st.error("Database connection failed. Please check your configuration.")
        return False

    tab1, tab2 = st.tabs(["Login", "Register"])

    auth = AuthService()

    with tab1:
        st.subheader("Welcome back!")

        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please enter email and password")
                else:
                    user = auth.login(email, password)
                    if user:
                        st.session_state.user_id = str(user.id)
                        st.session_state.user_email = user.email
                        st.rerun()
                    else:
                        st.error("Invalid email or password")

    with tab2:
        st.subheader("Create an account")

        with st.form("register_form"):
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            password_confirm = st.text_input("Confirm Password", type="password", key="register_password_confirm")
            submitted = st.form_submit_button("Register", use_container_width=True)

            if submitted:
                if not email:
                    st.error("Please enter an email address")
                elif not validate_email(email):
                    st.error("Please enter a valid email address")
                elif not password:
                    st.error("Please enter a password")
                elif len(password) < MIN_PASSWORD_LENGTH:
                    st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
                elif password != password_confirm:
                    st.error("Passwords do not match")
                else:
                    try:
                        user = auth.register(email, password)
                        st.session_state.user_id = str(user.id)
                        st.session_state.user_email = user.email
                        st.success("Account created! Redirecting...")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    return False


def show_user_menu():
    """Show user menu in sidebar."""
    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.user_email}")

        if st.button("Logout", use_container_width=True):
            del st.session_state.user_id
            del st.session_state.user_email
            st.rerun()

        with st.expander("Change Password"):
            with st.form("change_password_form"):
                old_pw = st.text_input("Current Password", type="password")
                new_pw = st.text_input("New Password", type="password")
                new_pw_confirm = st.text_input("Confirm New Password", type="password")
                submitted = st.form_submit_button("Change Password")

                if submitted:
                    if not old_pw or not new_pw:
                        st.error("Please fill in all fields")
                    elif len(new_pw) < MIN_PASSWORD_LENGTH:
                        st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
                    elif new_pw != new_pw_confirm:
                        st.error("New passwords do not match")
                    else:
                        auth = AuthService()
                        from uuid import UUID
                        if auth.change_password(UUID(st.session_state.user_id), old_pw, new_pw):
                            st.success("Password changed!")
                        else:
                            st.error("Current password is incorrect")
```

**Step 3: Modify main() to check authentication**

Find the main app entry point and wrap it with auth check. The pattern is:

```python
def main():
    st.set_page_config(...)

    # Auth check - show login if not authenticated
    if "user_id" not in st.session_state:
        show_auth_page()
        return

    # User is authenticated - show user menu
    show_user_menu()

    # Initialize storage with user's ID
    from uuid import UUID
    storage = DatabaseStorage(UUID(st.session_state.user_id))

    # ... rest of existing app code, replacing WebStorage() with storage ...
```

**Step 4: Replace WebStorage with DatabaseStorage**

Throughout app.py, replace:
- `WebStorage()` → `storage` (the DatabaseStorage instance)
- `init_web_storage()` → (remove, no longer needed)
- `sync_to_localstorage()` → (remove, no longer needed)

**Step 5: Commit**

```bash
git add src/ui/app.py
git commit -m "feat: add login/register UI and integrate database storage"
```

---

## Task 8: Integration Testing

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
"""Integration tests for full auth + storage flow.

Requires DATABASE_URL to be set to a test database.
Run with: pytest tests/test_integration.py -v
"""

import os
import pytest
from uuid import UUID

# Skip if no database URL
pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set"
)


@pytest.fixture
def clean_db():
    """Provide a clean database state."""
    from src.core.database import get_cursor, init_database

    # Initialize schema
    init_database()

    yield

    # Cleanup - delete test users
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE email LIKE 'test_%@example.com'")


class TestFullAuthFlow:
    """Test complete authentication flow."""

    def test_register_login_flow(self, clean_db):
        """Should register and login successfully."""
        from src.core.auth import AuthService

        auth = AuthService()
        email = "test_flow@example.com"
        password = "testpassword123"

        # Register
        user = auth.register(email, password)
        assert user.email == email
        assert user.id is not None

        # Login
        logged_in = auth.login(email, password)
        assert logged_in is not None
        assert logged_in.id == user.id

    def test_storage_with_auth(self, clean_db):
        """Should store and retrieve cards for authenticated user."""
        from src.core.auth import AuthService
        from src.core.db_storage import DatabaseStorage
        from src.core.models import Card
        from datetime import datetime

        # Create user
        auth = AuthService()
        user = auth.register("test_storage@example.com", "testpassword123")

        # Create storage for user
        storage = DatabaseStorage(user.id)

        # Add a card
        from src.core.library import CardTemplate
        from src.core.models import Credit

        template = CardTemplate(
            id="test-card",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=95,
            credits=[Credit(name="Test Credit", amount=10, frequency="monthly")],
        )

        card = storage.add_card_from_template(template, opened_date=None)

        # Retrieve cards
        cards = storage.get_all_cards()
        assert len(cards) == 1
        assert cards[0].name == "Test Card"

        # Delete card
        assert storage.delete_card(card.id) is True
        assert len(storage.get_all_cards()) == 0

    def test_user_isolation(self, clean_db):
        """Should isolate data between users."""
        from src.core.auth import AuthService
        from src.core.db_storage import DatabaseStorage
        from src.core.library import CardTemplate

        auth = AuthService()

        # Create two users
        user1 = auth.register("test_user1@example.com", "password123")
        user2 = auth.register("test_user2@example.com", "password123")

        storage1 = DatabaseStorage(user1.id)
        storage2 = DatabaseStorage(user2.id)

        # User 1 adds a card
        template = CardTemplate(id="t1", name="User1 Card", issuer="Bank", annual_fee=0, credits=[])
        storage1.add_card_from_template(template)

        # User 2 should see no cards
        assert len(storage1.get_all_cards()) == 1
        assert len(storage2.get_all_cards()) == 0
```

**Step 2: Run integration tests (requires database)**

```bash
# Set DATABASE_URL first
python -m pytest tests/test_integration.py -v
```

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for auth and storage"
```

---

## Final Checklist

- [ ] Dependencies added to requirements.txt
- [ ] .env.example created
- [ ] database.py with schema
- [ ] init_db.py script
- [ ] User model in models.py
- [ ] auth.py with AuthService
- [ ] db_storage.py with DatabaseStorage
- [ ] Login/register UI in app.py
- [ ] WebStorage replaced with DatabaseStorage
- [ ] All tests passing
- [ ] Integration tested with real database
