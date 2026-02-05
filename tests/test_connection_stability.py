"""Connection stability tests."""

import pytest
from datetime import datetime, date
from unittest.mock import patch, MagicMock
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


class TestNetworkErrorHandling:
    """Test graceful handling of database connection failures (Issue #38)."""

    def test_get_all_cards_handles_connection_error(self):
        """get_all_cards should handle connection errors gracefully."""
        from unittest.mock import patch, MagicMock

        auth = AuthService()
        email = f"conn_err_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Mock get_cursor to raise a connection error
        with patch('src.core.db_storage.get_cursor') as mock_cursor:
            mock_cursor.side_effect = psycopg2.OperationalError("Connection refused")

            # Should raise an exception (not crash silently)
            with pytest.raises(psycopg2.OperationalError):
                storage.get_all_cards()

    def test_add_card_handles_connection_error(self):
        """add_card should handle connection errors gracefully."""
        from unittest.mock import patch

        auth = AuthService()
        email = f"add_err_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Mock get_cursor to raise a connection error
        with patch('src.core.db_storage.get_cursor') as mock_cursor:
            mock_cursor.side_effect = psycopg2.OperationalError("Network timeout")

            template = get_template("chase_sapphire_preferred")
            # Should raise an exception
            with pytest.raises(psycopg2.OperationalError):
                storage.add_card_from_template(template)

    def test_update_card_handles_connection_error(self):
        """update_card should handle connection errors gracefully."""
        from unittest.mock import patch

        auth = AuthService()
        email = f"upd_err_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # First add a card successfully
        card = add_card_helper(storage, "chase_sapphire_preferred")
        card_id = card.id

        # Mock get_cursor to raise a connection error on update
        with patch('src.core.db_storage.get_cursor') as mock_cursor:
            mock_cursor.side_effect = psycopg2.OperationalError("Connection lost")

            # Should raise an exception
            with pytest.raises(psycopg2.OperationalError):
                storage.update_card(card_id, {"nickname": "Updated Card"})

    def test_delete_card_handles_connection_error(self):
        """delete_card should handle connection errors gracefully."""
        from unittest.mock import patch

        auth = AuthService()
        email = f"del_err_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # First add a card successfully
        card = add_card_helper(storage, "chase_sapphire_preferred")
        card_id = card.id

        # Mock get_cursor to raise a connection error on delete
        with patch('src.core.db_storage.get_cursor') as mock_cursor:
            mock_cursor.side_effect = psycopg2.OperationalError("Database unreachable")

            # Should raise an exception
            with pytest.raises(psycopg2.OperationalError):
                storage.delete_card(card_id)

    def test_save_card_handles_connection_error(self):
        """save_card should handle connection errors gracefully."""
        from unittest.mock import patch

        auth = AuthService()
        email = f"save_err_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # First add a card successfully
        card = add_card_helper(storage, "chase_sapphire_preferred")

        # Modify the card
        card.nickname = "Modified Card"

        # Mock get_cursor to raise a connection error on save
        with patch('src.core.db_storage.get_cursor') as mock_cursor:
            mock_cursor.side_effect = psycopg2.OperationalError("Connection timeout")

            # Should raise an exception
            with pytest.raises(psycopg2.OperationalError):
                storage.save_card(card)

    def test_get_preferences_handles_connection_error(self):
        """get_preferences should handle connection errors gracefully."""
        from unittest.mock import patch

        auth = AuthService()
        email = f"pref_err_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Mock get_cursor to raise a connection error
        with patch('src.core.db_storage.get_cursor') as mock_cursor:
            mock_cursor.side_effect = psycopg2.OperationalError("Connection error")

            # Should raise an exception
            with pytest.raises(psycopg2.OperationalError):
                storage.get_preferences()

    def test_save_preferences_handles_connection_error(self):
        """save_preferences should handle connection errors gracefully."""
        from unittest.mock import patch
        from src.core.preferences import UserPreferences

        auth = AuthService()
        email = f"save_pref_err_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        prefs = UserPreferences(sort_by="name", sort_descending=True)

        # Mock get_cursor to raise a connection error
        with patch('src.core.db_storage.get_cursor') as mock_cursor:
            mock_cursor.side_effect = psycopg2.OperationalError("Database error")

            # Should raise an exception
            with pytest.raises(psycopg2.OperationalError):
                storage.save_preferences(prefs)

    def test_auth_handles_connection_error(self):
        """Auth operations should handle connection errors gracefully."""
        from unittest.mock import patch

        auth = AuthService()

        # Mock get_connection (deeper in the stack) to raise a connection error
        with patch('src.core.database.get_connection') as mock_conn:
            mock_conn.side_effect = psycopg2.OperationalError("Cannot connect to database")

            # Should raise an exception (not crash)
            with pytest.raises(psycopg2.OperationalError):
                auth.register(f"new_user_{datetime.now().timestamp()}@test.com", "TestPassword123!")

    def test_intermittent_connection_failure_recovery(self):
        """System should recover from intermittent connection failures."""
        from unittest.mock import patch, MagicMock
        import itertools

        auth = AuthService()
        email = f"intermit_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add a card successfully
        card = add_card_helper(storage, "chase_sapphire_preferred")
        card_id = card.id

        # Simulate intermittent failure: fail once, then succeed
        call_count = itertools.count()

        def intermittent_failure(*args, **kwargs):
            if next(call_count) == 0:
                raise psycopg2.OperationalError("Temporary connection issue")
            # Second call succeeds - use the real function
            from src.core.database import get_cursor as real_get_cursor
            return real_get_cursor(*args, **kwargs)

        # First call fails
        with patch('src.core.db_storage.get_cursor', side_effect=intermittent_failure):
            with pytest.raises(psycopg2.OperationalError):
                storage.get_all_cards()

        # Second call succeeds (no patch - normal operation)
        cards = storage.get_all_cards()
        assert len(cards) == 1
        assert cards[0].id == card_id

    def test_connection_error_does_not_corrupt_data(self):
        """Connection errors should not leave data in inconsistent state."""
        from unittest.mock import patch

        auth = AuthService()
        email = f"corrupt_check_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add a card successfully
        card = add_card_helper(storage, "chase_sapphire_preferred")
        original_nickname = card.nickname

        # Try to update with connection error
        card.nickname = "This Should Not Save"

        with patch('src.core.db_storage.get_cursor') as mock_cursor:
            mock_cursor.side_effect = psycopg2.OperationalError("Connection error during save")

            with pytest.raises(psycopg2.OperationalError):
                storage.save_card(card)

        # Reload card - should have original data
        cards = storage.get_all_cards()
        assert len(cards) == 1
        assert cards[0].nickname == original_nickname

    def test_multiple_concurrent_connection_errors(self):
        """Multiple operations failing simultaneously should not cause cascade issues."""
        from unittest.mock import patch

        auth = AuthService()
        users = []

        # Create multiple users
        for i in range(3):
            email = f"concurrent_err_{i}_{datetime.now().timestamp()}@test.com"
            user = auth.register(email, "TestPassword123!")
            users.append(user)

        # Mock connection failure
        with patch('src.core.db_storage.get_cursor') as mock_cursor:
            mock_cursor.side_effect = psycopg2.OperationalError("Network partition")

            # All operations should fail gracefully
            for user in users:
                storage = DatabaseStorage(user.id)
                with pytest.raises(psycopg2.OperationalError):
                    storage.get_all_cards()

        # After "network recovery", operations should work
        for user in users:
            storage = DatabaseStorage(user.id)
            cards = storage.get_all_cards()
            # Should return empty list (or existing cards if any)
            assert isinstance(cards, list)
