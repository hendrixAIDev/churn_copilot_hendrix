"""Unit tests for user preferences.

Run with: pytest tests/test_preferences.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.core.preferences import UserPreferences, PreferencesStorage


class TestUserPreferences:
    """Tests for UserPreferences model."""

    def test_default_preferences(self):
        """Test default preference values."""
        prefs = UserPreferences()

        assert prefs.sort_by == "date_added"
        assert prefs.sort_descending is True
        assert prefs.group_by_issuer is False

    def test_custom_preferences(self):
        """Test creating preferences with custom values."""
        prefs = UserPreferences(
            sort_by="name_asc",
            sort_descending=False,
            group_by_issuer=True,
        )

        assert prefs.sort_by == "name_asc"
        assert prefs.sort_descending is False
        assert prefs.group_by_issuer is True


class TestPreferencesStorage:
    """Tests for PreferencesStorage."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        storage = PreferencesStorage(data_dir=temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_default_preferences(self, temp_storage):
        """Test getting preferences when file doesn't exist."""
        prefs = temp_storage.get_preferences()

        assert prefs.sort_by == "date_added"
        assert prefs.group_by_issuer is False

    def test_save_and_load_preferences(self, temp_storage):
        """Test saving and loading preferences."""
        prefs = UserPreferences(
            sort_by="fee_desc",
            group_by_issuer=True,
        )
        temp_storage.save_preferences(prefs)

        # Load and verify
        loaded = temp_storage.get_preferences()
        assert loaded.sort_by == "fee_desc"
        assert loaded.group_by_issuer is True

    def test_update_single_preference(self, temp_storage):
        """Test updating a single preference."""
        temp_storage.update_preference("group_by_issuer", True)

        prefs = temp_storage.get_preferences()
        assert prefs.group_by_issuer is True
        # Other preferences should remain default
        assert prefs.sort_by == "date_added"

    def test_preferences_persist_across_instances(self, temp_storage):
        """Test that preferences persist across storage instances."""
        prefs = UserPreferences(sort_by="name_asc", group_by_issuer=True)
        temp_storage.save_preferences(prefs)

        # Create new storage instance pointing to same directory
        new_storage = PreferencesStorage(data_dir=temp_storage.data_dir)
        loaded = new_storage.get_preferences()

        assert loaded.sort_by == "name_asc"
        assert loaded.group_by_issuer is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
