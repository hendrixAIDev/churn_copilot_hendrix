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
        assert "CREATE TABLE" in sql or "CREATE TABLE IF NOT EXISTS" in sql

    def test_schema_contains_users_table(self):
        """Should contain users table definition."""
        from src.core.database import get_schema_sql

        sql = get_schema_sql()
        assert "users" in sql.lower()
        assert "email" in sql.lower()
        assert "password_hash" in sql.lower()

    def test_schema_contains_cards_table(self):
        """Should contain cards table definition."""
        from src.core.database import get_schema_sql

        sql = get_schema_sql()
        assert "cards" in sql.lower()
        assert "user_id" in sql.lower()

    def test_schema_contains_user_preferences_table(self):
        """Should contain user_preferences table definition."""
        from src.core.database import get_schema_sql

        sql = get_schema_sql()
        assert "user_preferences" in sql.lower()


class TestDatabaseHelpers:
    """Test database helper functions."""

    def test_check_connection_returns_bool(self):
        """check_connection should return boolean."""
        from src.core.database import check_connection

        # Without a real database, this should return False
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("DATABASE_URL", None)
            result = check_connection()
            assert isinstance(result, bool)
            assert result is False  # Should fail without DATABASE_URL

    @patch('src.core.database.psycopg2.connect')
    def test_get_connection_uses_database_url(self, mock_connect):
        """get_connection should use DATABASE_URL."""
        from src.core.database import get_connection

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/testdb"}):
            with get_connection() as conn:
                pass

        mock_connect.assert_called_once_with("postgresql://test:test@localhost/testdb")
        mock_conn.close.assert_called_once()

    @patch('src.core.database.psycopg2.connect')
    def test_get_cursor_commits_on_success(self, mock_connect):
        """get_cursor should commit on successful exit."""
        from src.core.database import get_cursor

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/testdb"}):
            with get_cursor() as cursor:
                cursor.execute("SELECT 1")

        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    @patch('src.core.database.psycopg2.connect')
    def test_get_cursor_rollback_on_error(self, mock_connect):
        """get_cursor should rollback on error."""
        from src.core.database import get_cursor

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:test@localhost/testdb"}):
            with pytest.raises(RuntimeError):
                with get_cursor() as cursor:
                    raise RuntimeError("Test error")

        mock_conn.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
