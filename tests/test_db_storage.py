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
