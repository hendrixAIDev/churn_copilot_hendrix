"""E2E tests for authentication using database backend."""

import pytest
from datetime import datetime
from uuid import UUID
import os

# Ensure DATABASE_URL is set for tests
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/churnpilot")

from src.core.auth import AuthService, validate_email, validate_password
from src.core.database import get_cursor, check_connection


class TestDatabaseConnection:
    """Verify database is accessible for E2E tests."""

    def test_database_is_connected(self):
        """Database should be reachable."""
        assert check_connection() is True, "Database must be running for E2E tests"


class TestUserRegistration:
    """Test user registration flow."""

    @pytest.fixture
    def auth_service(self):
        """Get auth service instance."""
        return AuthService()

    @pytest.fixture
    def unique_email(self):
        """Generate unique email for test."""
        return f"test_{datetime.now().timestamp()}@test.com"

    def test_registration_with_valid_credentials(self, auth_service, unique_email):
        """New user should be able to register with valid email/password."""
        password = "TestPassword123!"

        user = auth_service.register(unique_email, password)

        assert user is not None
        assert user.email == unique_email.lower()
        assert isinstance(user.id, UUID)

    def test_registration_creates_user_in_database(self, auth_service, unique_email):
        """Registered user should exist in database."""
        password = "TestPassword123!"
        user = auth_service.register(unique_email, password)

        with get_cursor(commit=False) as cur:
            cur.execute("SELECT email FROM users WHERE id = %s", (str(user.id),))
            row = cur.fetchone()

        assert row is not None
        assert row["email"] == unique_email.lower()

    def test_registration_duplicate_email_fails(self, auth_service, unique_email):
        """Duplicate email should raise ValueError."""
        password = "TestPassword123!"

        # First registration should succeed
        auth_service.register(unique_email, password)

        # Second registration with same email should fail
        with pytest.raises(ValueError, match="already exists|already registered"):
            auth_service.register(unique_email, "DifferentPassword123!")

    def test_registration_invalid_email_fails(self, auth_service):
        """Invalid email format should raise ValueError."""
        with pytest.raises(ValueError, match="[Ii]nvalid email"):
            auth_service.register("not-an-email", "TestPassword123!")

    def test_registration_short_password_fails(self, auth_service, unique_email):
        """Password less than 8 chars should raise ValueError."""
        with pytest.raises(ValueError, match="[Pp]assword"):
            auth_service.register(unique_email, "short")

    def test_registration_empty_password_fails(self, auth_service, unique_email):
        """Empty password should raise ValueError."""
        with pytest.raises(ValueError, match="[Pp]assword"):
            auth_service.register(unique_email, "")


class TestUserLogin:
    """Test user login flow."""

    @pytest.fixture
    def auth_service(self):
        """Get auth service instance."""
        return AuthService()

    @pytest.fixture
    def registered_user(self, auth_service):
        """Create a registered user for login tests."""
        email = f"login_test_{datetime.now().timestamp()}@test.com"
        password = "TestPassword123!"
        user = auth_service.register(email, password)
        return {"email": email, "password": password, "user": user}

    def test_login_with_valid_credentials(self, auth_service, registered_user):
        """Valid credentials should return user."""
        user = auth_service.login(
            registered_user["email"],
            registered_user["password"]
        )

        assert user is not None
        assert user.email == registered_user["email"].lower()
        assert user.id == registered_user["user"].id

    def test_login_wrong_password_fails(self, auth_service, registered_user):
        """Wrong password should return None."""
        result = auth_service.login(registered_user["email"], "WrongPassword123!")
        assert result is None, "Wrong password should return None"

    def test_login_nonexistent_email_fails(self, auth_service):
        """Nonexistent email should return None."""
        result = auth_service.login("nonexistent@test.com", "SomePassword123!")
        assert result is None, "Nonexistent email should return None"

    def test_login_case_insensitive_email(self, auth_service, registered_user):
        """Email should be case-insensitive for login."""
        # Try logging in with uppercase email
        upper_email = registered_user["email"].upper()
        user = auth_service.login(upper_email, registered_user["password"])

        assert user is not None
        assert user.id == registered_user["user"].id

    def test_login_email_with_whitespace_trimmed(self, auth_service, registered_user):
        """Email with leading/trailing whitespace should work."""
        padded_email = f"  {registered_user['email']}  "
        user = auth_service.login(padded_email, registered_user["password"])

        assert user is not None
        assert user.id == registered_user["user"].id


class TestPasswordChange:
    """Test password change flow."""

    @pytest.fixture
    def auth_service(self):
        """Get auth service instance."""
        return AuthService()

    @pytest.fixture
    def registered_user(self, auth_service):
        """Create a registered user."""
        email = f"pwchange_test_{datetime.now().timestamp()}@test.com"
        password = "OldPassword123!"
        user = auth_service.register(email, password)
        return {"email": email, "password": password, "user": user}

    def test_change_password_success(self, auth_service, registered_user):
        """Should be able to change password with correct old password."""
        new_password = "NewPassword456!"

        result = auth_service.change_password(
            registered_user["user"].id,
            registered_user["password"],
            new_password
        )

        assert result is True

        # Should be able to login with new password
        user = auth_service.login(registered_user["email"], new_password)
        assert user is not None

    def test_change_password_wrong_old_password_fails(self, auth_service, registered_user):
        """Should fail if old password is wrong."""
        result = auth_service.change_password(
            registered_user["user"].id,
            "WrongOldPassword!",
            "NewPassword456!"
        )

        assert result is False

        # Old password should still work
        user = auth_service.login(registered_user["email"], registered_user["password"])
        assert user is not None


class TestEmailValidation:
    """Test email validation edge cases."""

    @pytest.mark.parametrize("email,expected", [
        ("user@example.com", True),
        ("user.name@domain.co.uk", True),
        ("user+tag@example.com", True),
        ("UPPERCASE@EXAMPLE.COM", True),
        ("a@b.co", True),
        ("", False),
        (" ", False),
        ("not-an-email", False),
        ("@example.com", False),
        ("user@", False),
        ("user@.com", False),
    ])
    def test_email_validation(self, email, expected):
        """Test various email formats."""
        assert validate_email(email) == expected


class TestPasswordValidation:
    """Test password validation edge cases."""

    @pytest.mark.parametrize("password,expected", [
        ("12345678", True),  # Exactly 8 chars
        ("longpassword123", True),
        ("1234567", False),  # 7 chars
        ("short", False),
        ("", False),
    ])
    def test_password_validation(self, password, expected):
        """Test various password lengths."""
        assert validate_password(password) == expected
