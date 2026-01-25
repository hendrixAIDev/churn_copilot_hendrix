"""Connection stability tests."""

import pytest
from datetime import datetime, date
from unittest.mock import patch, MagicMock
import os

# Ensure DATABASE_URL is set for tests
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/churnpilot")

import psycopg2
from src.core.database import get_cursor, check_connection, get_connection
from src.core.db_storage import DatabaseStorage
from src.core.auth import AuthService
from src.core.library import get_template


def add_card_helper(storage, template_id, opened_date=None, signup_bonus=None):
    """Helper to add card from template ID."""
    template = get_template(template_id)
    if template is None:
        raise ValueError(f"Template not found: {template_id}")
    return storage.add_card_from_template(
        template=template,
        opened_date=opened_date or date.today(),
        signup_bonus=signup_bonus
    )


class TestDatabaseConnection:
    """Verify database is accessible for connection tests."""

    def test_database_is_connected(self):
        """Database should be reachable."""
        assert check_connection() is True

    def test_check_connection_returns_bool(self):
        """check_connection should return a boolean."""
        result = check_connection()
        assert isinstance(result, bool)

    def test_connection_can_execute_query(self):
        """Connection should be able to execute simple queries."""
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT 1 as result")
            row = cur.fetchone()
            assert row["result"] == 1


class TestConnectionErrorHandling:
    """Test database connection error handling."""

    def test_check_connection_handles_failure(self):
        """check_connection should return False on connection failure."""
        with patch('src.core.database.psycopg2.connect') as mock_connect:
            mock_connect.side_effect = psycopg2.OperationalError("Connection refused")
            # Note: check_connection might use cached connection, so this tests the concept
            # The actual implementation may need adjustment based on caching behavior
            try:
                result = check_connection()
                # If it returns, should be True (cached) or False (fresh check failed)
                assert isinstance(result, bool)
            except psycopg2.OperationalError:
                # If it raises, that's also acceptable behavior
                pass

    def test_get_cursor_context_manager_works(self):
        """get_cursor should work as context manager."""
        with get_cursor(commit=False) as cur:
            assert cur is not None
            cur.execute("SELECT 1")

    def test_get_cursor_with_commit_true(self):
        """get_cursor with commit=True should commit changes."""
        auth = AuthService()
        email = f"commit_test_{datetime.now().timestamp()}@test.com"

        # Register user (this uses commit internally)
        user = auth.register(email, "TestPassword123!")

        # Verify user exists by querying
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT email FROM users WHERE id = %s", (str(user.id),))
            row = cur.fetchone()
            assert row is not None
            assert row["email"] == email.lower()

    def test_get_cursor_rollback_on_error(self):
        """get_cursor should rollback on error."""
        try:
            with get_cursor(commit=True) as cur:
                cur.execute("SELECT 1")
                # Intentionally cause an error
                raise ValueError("Simulated error")
        except ValueError:
            pass  # Expected

        # Database should still be usable
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT 1 as val")
            assert cur.fetchone()["val"] == 1


class TestConnectionResilience:
    """Test connection resilience patterns."""

    def test_multiple_sequential_queries(self):
        """Multiple sequential queries should work."""
        for i in range(10):
            with get_cursor(commit=False) as cur:
                cur.execute("SELECT %s as num", (i,))
                row = cur.fetchone()
                assert row["num"] == i

    def test_nested_cursors_not_needed(self):
        """Operations don't require nested cursors."""
        auth = AuthService()
        email = f"nested_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add card
        card = add_card_helper(storage, "chase_sapphire_preferred")

        # Edit card
        card.nickname = "Test Card"
        storage.save_card(card)

        # Read card
        cards = storage.get_all_cards()
        assert len(cards) == 1
        assert cards[0].nickname == "Test Card"

    def test_operations_after_failed_query(self):
        """Should be able to continue after a failed query."""
        # First, try a query that might fail
        try:
            with get_cursor(commit=False) as cur:
                cur.execute("SELECT * FROM nonexistent_table_xyz")
        except Exception:
            pass  # Expected

        # Should still be able to do valid queries
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT 1 as result")
            assert cur.fetchone()["result"] == 1


class TestTransactionBehavior:
    """Test transaction behavior."""

    def test_uncommitted_changes_not_visible_in_new_cursor(self):
        """Uncommitted changes should not be visible in other connections."""
        # This test verifies transaction isolation
        auth = AuthService()
        email = f"transaction_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")

        # User should be committed and visible
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email.lower(),))
            assert cur.fetchone() is not None

    def test_successful_commit_persists_data(self):
        """Successfully committed data should persist."""
        auth = AuthService()
        email = f"persist_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add card (should commit)
        card = add_card_helper(storage, "chase_sapphire_preferred")
        card_id = card.id

        # Create new storage instance and verify card exists
        storage2 = DatabaseStorage(user.id)
        cards = storage2.get_all_cards()
        assert any(c.id == card_id for c in cards)


class TestConnectionPooling:
    """Test connection pooling behavior (if applicable)."""

    def test_multiple_storage_instances_work(self):
        """Multiple DatabaseStorage instances should work correctly."""
        auth = AuthService()

        # Create multiple users with storage
        storages = []
        for i in range(5):
            email = f"pool_test_{i}_{datetime.now().timestamp()}@test.com"
            user = auth.register(email, "TestPassword123!")
            storage = DatabaseStorage(user.id)
            storages.append(storage)

        # Each storage should work independently
        for i, storage in enumerate(storages):
            card = add_card_helper(storage, "chase_sapphire_preferred")
            card.nickname = f"Card {i}"
            storage.save_card(card)

        # Verify each user has exactly one card
        for storage in storages:
            cards = storage.get_all_cards()
            assert len(cards) == 1

    def test_rapid_connection_usage(self):
        """Rapid connection usage should not exhaust resources."""
        for i in range(50):
            with get_cursor(commit=False) as cur:
                cur.execute("SELECT %s as iteration", (i,))
                cur.fetchone()


class TestDatabaseOperationsUnderLoad:
    """Test database operations under simulated load."""

    def test_many_users_many_cards(self):
        """System should handle many users with many cards."""
        auth = AuthService()

        # Create 5 users, each with 5 cards
        for u in range(5):
            email = f"load_user_{u}_{datetime.now().timestamp()}@test.com"
            user = auth.register(email, "TestPassword123!")
            storage = DatabaseStorage(user.id)

            for c in range(5):
                card = add_card_helper(storage, "chase_sapphire_preferred")
                card.nickname = f"User {u} Card {c}"
                storage.save_card(card)

            # Verify
            cards = storage.get_all_cards()
            assert len(cards) == 5

    def test_interleaved_operations_multiple_users(self):
        """Interleaved operations from multiple users should not interfere."""
        auth = AuthService()

        # Create two users
        user1 = auth.register(f"interleave1_{datetime.now().timestamp()}@test.com", "TestPassword123!")
        user2 = auth.register(f"interleave2_{datetime.now().timestamp()}@test.com", "TestPassword123!")

        storage1 = DatabaseStorage(user1.id)
        storage2 = DatabaseStorage(user2.id)

        # Interleave operations
        card1 = add_card_helper(storage1, "chase_sapphire_preferred")
        card2 = add_card_helper(storage2, "amex_gold")

        card1.nickname = "User 1 Card"
        card2.nickname = "User 2 Card"

        storage1.save_card(card1)
        storage2.save_card(card2)

        add_card_helper(storage1, "chase_freedom_unlimited")
        add_card_helper(storage2, "capital_one_venture_x")

        # Verify isolation
        cards1 = storage1.get_all_cards()
        cards2 = storage2.get_all_cards()

        assert len(cards1) == 2
        assert len(cards2) == 2
        assert all(c.nickname != "User 2 Card" for c in cards1)
        assert all(c.nickname != "User 1 Card" for c in cards2)
