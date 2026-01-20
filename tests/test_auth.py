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
