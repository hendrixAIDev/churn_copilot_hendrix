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


class TestRateLimiting:
    """Test rate limiting for login, signup, and feedback."""

    def setup_method(self):
        """Clear rate limit storage before each test."""
        from src.core import rate_limit
        rate_limit._login_attempts.clear()
        rate_limit._signup_attempts.clear()
        rate_limit._feedback_attempts.clear()

    def test_login_rate_limit_allows_under_limit(self):
        """Should allow login attempts under the limit."""
        from src.core.rate_limit import check_login_rate_limit, record_login_failure

        email = "test@example.com"

        # First 4 attempts should be allowed
        for i in range(4):
            allowed, msg = check_login_rate_limit(email)
            assert allowed is True
            assert msg == ""
            record_login_failure(email)

    def test_login_rate_limit_blocks_after_max_attempts(self):
        """Should block login after 5 failed attempts."""
        from src.core.rate_limit import check_login_rate_limit, record_login_failure

        email = "test@example.com"

        # Fail 5 times
        for i in range(5):
            allowed, msg = check_login_rate_limit(email)
            record_login_failure(email)

        # 6th attempt should be blocked
        allowed, msg = check_login_rate_limit(email)
        assert allowed is False
        assert "Too many login attempts" in msg
        assert "minute" in msg

    def test_login_rate_limit_reset_on_success(self):
        """Should reset rate limit on successful login."""
        from src.core.rate_limit import (
            check_login_rate_limit,
            record_login_failure,
            reset_login_attempts,
        )

        email = "test@example.com"

        # Fail 3 times
        for i in range(3):
            check_login_rate_limit(email)
            record_login_failure(email)

        # Successful login resets counter
        reset_login_attempts(email)

        # Should allow new attempts
        allowed, msg = check_login_rate_limit(email)
        assert allowed is True

    def test_signup_rate_limit_allows_under_limit(self):
        """Should allow signup attempts under the limit."""
        from src.core.rate_limit import check_signup_rate_limit, record_signup_attempt

        session_id = "test_session_123"

        # First 2 attempts should be allowed
        for i in range(2):
            allowed, msg = check_signup_rate_limit(session_id)
            assert allowed is True
            assert msg == ""
            record_signup_attempt(session_id)

    def test_signup_rate_limit_blocks_after_max_attempts(self):
        """Should block signup after 3 attempts."""
        from src.core.rate_limit import check_signup_rate_limit, record_signup_attempt

        session_id = "test_session_123"

        # Attempt 3 times
        for i in range(3):
            allowed, msg = check_signup_rate_limit(session_id)
            record_signup_attempt(session_id)

        # 4th attempt should be blocked
        allowed, msg = check_signup_rate_limit(session_id)
        assert allowed is False
        assert "Too many signup attempts" in msg
        assert "hour" in msg

    def test_feedback_rate_limit_allows_under_limit(self):
        """Should allow feedback submissions under the limit."""
        from src.core.rate_limit import (
            check_feedback_rate_limit,
            record_feedback_submission,
        )

        user_id = "test_user_123"

        # First 4 submissions should be allowed
        for i in range(4):
            allowed, msg = check_feedback_rate_limit(user_id)
            assert allowed is True
            assert msg == ""
            record_feedback_submission(user_id)

    def test_feedback_rate_limit_blocks_after_max_attempts(self):
        """Should block feedback after 5 submissions."""
        from src.core.rate_limit import (
            check_feedback_rate_limit,
            record_feedback_submission,
        )

        user_id = "test_user_123"

        # Submit 5 times
        for i in range(5):
            allowed, msg = check_feedback_rate_limit(user_id)
            record_feedback_submission(user_id)

        # 6th attempt should be blocked
        allowed, msg = check_feedback_rate_limit(user_id)
        assert allowed is False
        assert "submitted several feedbacks recently" in msg

    def test_rate_limit_lockout_expires(self):
        """Should allow login after lockout period expires."""
        from src.core.rate_limit import check_login_rate_limit, record_login_failure
        from datetime import datetime, timedelta
        from src.core import rate_limit

        email = "test@example.com"

        # Trigger lockout
        for i in range(5):
            check_login_rate_limit(email)
            record_login_failure(email)

        # Verify locked
        allowed, msg = check_login_rate_limit(email)
        assert allowed is False

        # Manually expire the lockout (simulate time passing)
        record = rate_limit._login_attempts[email]
        record["locked_until"] = datetime.utcnow() - timedelta(minutes=1)

        # Should now be allowed
        allowed, msg = check_login_rate_limit(email)
        assert allowed is True
