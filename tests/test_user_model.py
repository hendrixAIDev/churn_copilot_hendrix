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
