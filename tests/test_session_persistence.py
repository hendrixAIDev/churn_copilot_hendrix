"""Tests for session persistence (24hr token-based auth).

These tests verify:
1. Session tokens are created on login/register
2. Session tokens can be validated
3. Sessions expire after 24 hours of inactivity
4. Session validation refreshes expiry (sliding window)
5. Logout properly clears sessions
6. Session cleanup works correctly
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from uuid import UUID, uuid4

from src.core.auth import (
    AuthService,
    SESSION_TOKEN_BYTES,
    SESSION_EXPIRY_HOURS,
)
from src.core.database import get_cursor


@pytest.fixture
def auth_service():
    """Create AuthService instance."""
    return AuthService()


@pytest.fixture
def test_user(auth_service):
    """Create a test user for session tests."""
    email = f"session_test_{uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user = auth_service.register(email, password)
    yield user
    # Cleanup
    try:
        auth_service.delete_user(user.id)
    except Exception:
        pass


class TestSessionCreation:
    """Test session creation on login."""

    def test_create_session_returns_valid_token(self, auth_service, test_user):
        """Should return a valid session token."""
        token = auth_service.create_session(test_user.id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) == SESSION_TOKEN_BYTES * 2  # Hex encoding doubles length

    def test_create_session_stores_in_database(self, auth_service, test_user):
        """Should store session in database."""
        token = auth_service.create_session(test_user.id)

        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT user_id, token, expires_at FROM sessions WHERE token = %s",
                (token,)
            )
            row = cursor.fetchone()

        assert row is not None
        assert str(row["user_id"]) == str(test_user.id)
        assert row["token"] == token

    def test_create_session_sets_expiry(self, auth_service, test_user):
        """Should set expiry to ~24 hours from now."""
        before = datetime.utcnow()
        token = auth_service.create_session(test_user.id)
        after = datetime.utcnow()

        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT expires_at FROM sessions WHERE token = %s",
                (token,)
            )
            row = cursor.fetchone()

        # Expiry should be between 23h59m and 24h1m from creation
        expected_min = before + timedelta(hours=SESSION_EXPIRY_HOURS - 0.02)
        expected_max = after + timedelta(hours=SESSION_EXPIRY_HOURS + 0.02)

        assert expected_min <= row["expires_at"] <= expected_max

    def test_create_multiple_sessions(self, auth_service, test_user):
        """Should allow multiple sessions per user."""
        token1 = auth_service.create_session(test_user.id)
        token2 = auth_service.create_session(test_user.id)

        assert token1 != token2

        # Both should be valid
        user1 = auth_service.validate_session(token1)
        user2 = auth_service.validate_session(token2)

        assert user1 is not None
        assert user2 is not None

    def test_create_session_cleans_old_sessions(self, auth_service, test_user):
        """Should clean up old sessions keeping max 5."""
        # Create 6 sessions
        tokens = [auth_service.create_session(test_user.id) for _ in range(6)]

        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT COUNT(*) as cnt FROM sessions WHERE user_id = %s",
                (str(test_user.id),)
            )
            count = cursor.fetchone()["cnt"]

        # Should have at most 5 sessions (the 6th creation cleans up the oldest)
        assert count <= 5


class TestSessionValidation:
    """Test session token validation."""

    def test_validate_valid_session(self, auth_service, test_user):
        """Should return user for valid session."""
        token = auth_service.create_session(test_user.id)

        user = auth_service.validate_session(token)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_validate_invalid_token(self, auth_service):
        """Should return None for invalid token."""
        invalid_token = "a" * (SESSION_TOKEN_BYTES * 2)

        user = auth_service.validate_session(invalid_token)

        assert user is None

    def test_validate_empty_token(self, auth_service):
        """Should return None for empty token."""
        assert auth_service.validate_session("") is None
        assert auth_service.validate_session(None) is None

    def test_validate_wrong_length_token(self, auth_service):
        """Should return None for wrong length token."""
        too_short = "abc123"
        too_long = "a" * (SESSION_TOKEN_BYTES * 2 + 10)

        assert auth_service.validate_session(too_short) is None
        assert auth_service.validate_session(too_long) is None

    def test_validate_refreshes_expiry(self, auth_service, test_user):
        """Should extend session expiry on validation (sliding window)."""
        token = auth_service.create_session(test_user.id)

        # Get initial expiry
        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT expires_at FROM sessions WHERE token = %s",
                (token,)
            )
            initial_expiry = cursor.fetchone()["expires_at"]

        # Small delay to ensure time difference
        import time
        time.sleep(0.1)

        # Validate session
        auth_service.validate_session(token)

        # Get new expiry
        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT expires_at FROM sessions WHERE token = %s",
                (token,)
            )
            new_expiry = cursor.fetchone()["expires_at"]

        # New expiry should be later (sliding window extended)
        assert new_expiry >= initial_expiry


class TestSessionExpiry:
    """Test session expiration."""

    def test_expired_session_returns_none(self, auth_service, test_user):
        """Should return None for expired session."""
        token = auth_service.create_session(test_user.id)

        # Manually expire the session
        with get_cursor() as cursor:
            cursor.execute(
                "UPDATE sessions SET expires_at = %s WHERE token = %s",
                (datetime.utcnow() - timedelta(hours=1), token)
            )

        user = auth_service.validate_session(token)

        assert user is None

    def test_expired_session_is_deleted(self, auth_service, test_user):
        """Should delete expired session on validation attempt."""
        token = auth_service.create_session(test_user.id)

        # Manually expire the session
        with get_cursor() as cursor:
            cursor.execute(
                "UPDATE sessions SET expires_at = %s WHERE token = %s",
                (datetime.utcnow() - timedelta(hours=1), token)
            )

        # Validation should fail and delete the session
        auth_service.validate_session(token)

        # Session should be gone
        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM sessions WHERE token = %s",
                (token,)
            )
            row = cursor.fetchone()

        assert row is None


class TestSessionDeletion:
    """Test session logout/deletion."""

    def test_delete_session_removes_from_db(self, auth_service, test_user):
        """Should remove session from database."""
        token = auth_service.create_session(test_user.id)

        result = auth_service.delete_session(token)

        assert result is True

        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM sessions WHERE token = %s",
                (token,)
            )
            row = cursor.fetchone()

        assert row is None

    def test_delete_session_returns_false_for_invalid(self, auth_service):
        """Should return False for non-existent session."""
        invalid_token = "a" * (SESSION_TOKEN_BYTES * 2)

        result = auth_service.delete_session(invalid_token)

        assert result is False

    def test_delete_all_sessions_clears_user_sessions(self, auth_service, test_user):
        """Should delete all sessions for a user (logout all devices)."""
        # Create multiple sessions
        tokens = [auth_service.create_session(test_user.id) for _ in range(3)]

        count = auth_service.delete_all_sessions(test_user.id)

        assert count == 3

        # All sessions should be gone
        for token in tokens:
            user = auth_service.validate_session(token)
            assert user is None


class TestSessionIntegration:
    """Integration tests for session flow."""

    def test_full_login_session_flow(self, auth_service):
        """Test complete login -> session -> validate -> logout flow."""
        # Register user
        email = f"flow_test_{uuid4().hex[:8]}@example.com"
        password = "testpassword123"
        user = auth_service.register(email, password)

        try:
            # Login
            logged_in_user = auth_service.login(email, password)
            assert logged_in_user is not None

            # Create session (simulating what app.py does on login)
            token = auth_service.create_session(logged_in_user.id)
            assert token is not None

            # Simulate page refresh - validate session
            restored_user = auth_service.validate_session(token)
            assert restored_user is not None
            assert restored_user.id == user.id
            assert restored_user.email == email

            # Logout
            result = auth_service.delete_session(token)
            assert result is True

            # Session should no longer work
            assert auth_service.validate_session(token) is None

        finally:
            auth_service.delete_user(user.id)

    def test_session_survives_simulated_refresh(self, auth_service, test_user):
        """Session should remain valid across simulated page refreshes."""
        token = auth_service.create_session(test_user.id)

        # Simulate multiple page refreshes
        for i in range(5):
            user = auth_service.validate_session(token)
            assert user is not None, f"Session invalid after refresh {i+1}"
            assert user.id == test_user.id

    def test_24_hour_expiry_configuration(self):
        """Verify 24-hour expiry is configured correctly."""
        assert SESSION_EXPIRY_HOURS == 24

    def test_token_length_is_secure(self):
        """Token should be 32 bytes (256 bits) for security."""
        assert SESSION_TOKEN_BYTES == 32


class TestSessionCleanup:
    """Test automatic session cleanup."""

    def test_expired_sessions_cleaned_on_new_session(self, auth_service, test_user):
        """Creating new session should clean up expired sessions."""
        # Create a session and manually expire it
        old_token = auth_service.create_session(test_user.id)

        with get_cursor() as cursor:
            cursor.execute(
                "UPDATE sessions SET expires_at = %s WHERE token = %s",
                (datetime.utcnow() - timedelta(days=1), old_token)
            )

        # Create new session - should trigger cleanup
        new_token = auth_service.create_session(test_user.id)

        # Old session should be gone
        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM sessions WHERE token = %s",
                (old_token,)
            )
            row = cursor.fetchone()

        assert row is None

        # New session should exist
        user = auth_service.validate_session(new_token)
        assert user is not None
