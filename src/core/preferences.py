"""User preferences storage for ChurnPilot."""

import json
from pathlib import Path
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    """User preferences for the application."""

    sort_by: str = Field(
        default="date_added",
        description="Sort order: 'date_added', 'date_opened', 'name', 'annual_fee'"
    )
    sort_descending: bool = Field(
        default=True,
        description="Sort in descending order"
    )
    group_by_issuer: bool = Field(
        default=False,
        description="Group cards by issuer"
    )


class PreferencesStorage:
    """JSON file-based storage for user preferences."""

    def __init__(self, data_dir: str | Path = "data"):
        """Initialize preferences storage.

        Args:
            data_dir: Directory to store preferences file.
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.prefs_file = self.data_dir / "preferences.json"

    def get_preferences(self) -> UserPreferences:
        """Load user preferences.

        Returns:
            UserPreferences object (defaults if file doesn't exist).
        """
        if not self.prefs_file.exists():
            return UserPreferences()

        try:
            content = self.prefs_file.read_text()
            data = json.loads(content)
            return UserPreferences.model_validate(data)
        except (json.JSONDecodeError, IOError):
            return UserPreferences()

    def save_preferences(self, prefs: UserPreferences) -> None:
        """Save user preferences.

        Args:
            prefs: UserPreferences to save.
        """
        try:
            self.prefs_file.write_text(
                json.dumps(prefs.model_dump(), indent=2)
            )
        except IOError:
            pass  # Silently fail - preferences are not critical

    def update_preference(self, key: str, value) -> UserPreferences:
        """Update a single preference.

        Args:
            key: Preference key to update.
            value: New value.

        Returns:
            Updated UserPreferences.
        """
        prefs = self.get_preferences()
        if hasattr(prefs, key):
            setattr(prefs, key, value)
            self.save_preferences(prefs)
        return prefs
