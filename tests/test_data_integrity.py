"""Data integrity tests."""

import pytest
from datetime import datetime, date
from uuid import uuid4

from src.core.database import get_cursor, check_connection
from src.core.db_storage import DatabaseStorage
from src.core.auth import AuthService
from src.core.models import SignupBonus
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
    """Verify database is accessible for integrity tests."""

    def test_database_is_connected(self):
        """Database should be reachable."""
        assert check_connection() is True


class TestForeignKeyIntegrity:
    """Test foreign key constraints are enforced."""

    def test_cards_require_valid_user(self):
        """Cannot insert card with fake user_id."""
        with pytest.raises(Exception):
            with get_cursor() as cur:
                cur.execute("""
                    INSERT INTO cards (id, user_id, name, issuer, opened_date)
                    VALUES (gen_random_uuid(), gen_random_uuid(), 'Test Card', 'Test Issuer', CURRENT_DATE)
                """)

    def test_signup_bonus_requires_valid_card(self):
        """Cannot insert signup bonus with fake card_id."""
        with pytest.raises(Exception):
            with get_cursor() as cur:
                cur.execute("""
                    INSERT INTO signup_bonuses (card_id, points_or_cash, spend_requirement, time_period_days)
                    VALUES (gen_random_uuid(), '50000 points', 4000, 90)
                """)

    def test_card_credits_require_valid_card(self):
        """Cannot insert card_credits with fake card_id."""
        with pytest.raises(Exception):
            with get_cursor() as cur:
                cur.execute("""
                    INSERT INTO card_credits (card_id, name, amount, frequency)
                    VALUES (gen_random_uuid(), 'Test Credit', 100, 'yearly')
                """)

    def test_delete_card_cascades_signup_bonus(self):
        """Deleting card should delete related signup bonus."""
        auth = AuthService()
        email = f"cascade_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Create card with signup bonus
        signup_bonus = SignupBonus(
            points_or_cash="75000 points",
            spend_requirement=5000,
            time_period_days=90,
            deadline=date(2026, 6, 1)
        )
        card = add_card_helper(storage, "chase_sapphire_preferred", signup_bonus=signup_bonus)

        # Verify signup bonus exists
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT card_id FROM signup_bonuses WHERE card_id = %s", (card.id,))
            assert cur.fetchone() is not None

        # Delete card
        storage.delete_card(card.id)

        # Verify signup bonus is gone
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT card_id FROM signup_bonuses WHERE card_id = %s", (card.id,))
            assert cur.fetchone() is None

    def test_delete_card_cascades_card_credits(self):
        """Deleting card should delete related card credits."""
        auth = AuthService()
        email = f"credit_cascade_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        card = add_card_helper(storage, "chase_sapphire_preferred")

        # Insert a credit directly for this card
        with get_cursor() as cur:
            cur.execute("""
                INSERT INTO card_credits (card_id, name, amount, frequency)
                VALUES (%s, 'Test Credit', 50.0, 'monthly')
            """, (card.id,))

        # Verify credit exists
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT card_id FROM card_credits WHERE card_id = %s", (card.id,))
            assert cur.fetchone() is not None

        # Delete card
        storage.delete_card(card.id)

        # Verify credit is gone
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT card_id FROM card_credits WHERE card_id = %s", (card.id,))
            assert cur.fetchone() is None


class TestUserIsolation:
    """Test users cannot see each other's data."""

    @pytest.fixture
    def two_users_with_cards(self):
        """Create two users each with cards."""
        auth = AuthService()

        # User A
        user_a = auth.register(
            f"isolation_a_{datetime.now().timestamp()}@test.com",
            "TestPassword123!"
        )
        storage_a = DatabaseStorage(user_a.id)
        card_a1 = add_card_helper(storage_a, "chase_sapphire_preferred")
        card_a2 = add_card_helper(storage_a, "amex_gold")

        # User B
        user_b = auth.register(
            f"isolation_b_{datetime.now().timestamp()}@test.com",
            "TestPassword123!"
        )
        storage_b = DatabaseStorage(user_b.id)
        card_b1 = add_card_helper(storage_b, "capital_one_venture_x")

        return {
            "storage_a": storage_a,
            "storage_b": storage_b,
            "cards_a": [card_a1, card_a2],
            "cards_b": [card_b1],
            "user_a_id": user_a.id,
            "user_b_id": user_b.id,
        }

    def test_user_only_sees_own_cards(self, two_users_with_cards):
        """User A should not see User B's cards."""
        storage_a = two_users_with_cards["storage_a"]
        storage_b = two_users_with_cards["storage_b"]

        cards_a = storage_a.get_all_cards()
        cards_b = storage_b.get_all_cards()

        assert len(cards_a) == 2
        assert len(cards_b) == 1

        # No overlap
        ids_a = {c.id for c in cards_a}
        ids_b = {c.id for c in cards_b}
        assert len(ids_a & ids_b) == 0

    def test_user_cannot_delete_other_user_cards(self, two_users_with_cards):
        """User A cannot delete User B's cards."""
        storage_a = two_users_with_cards["storage_a"]
        cards_b = two_users_with_cards["cards_b"]

        # User A tries to delete User B's card
        storage_a.delete_card(cards_b[0].id)

        # User B's card should still exist
        storage_b = two_users_with_cards["storage_b"]
        remaining = storage_b.get_all_cards()
        assert len(remaining) == 1
        assert remaining[0].id == cards_b[0].id

    def test_user_cannot_edit_other_user_cards(self, two_users_with_cards):
        """User A cannot edit User B's cards."""
        storage_a = two_users_with_cards["storage_a"]
        storage_b = two_users_with_cards["storage_b"]
        cards_b = two_users_with_cards["cards_b"]

        # Get User B's card and try to modify it via User A's storage
        card_b = cards_b[0]
        original_nickname = card_b.nickname
        card_b.nickname = "Hacked by User A"

        # This should either fail or not affect User B's data
        try:
            storage_a.save_card(card_b)
        except Exception:
            pass  # Expected - can't save another user's card

        # Reload from User B's perspective
        reloaded = storage_b.get_all_cards()[0]
        # Either nickname is unchanged OR the save silently failed
        # The important thing is User B's data is not corrupted
        assert reloaded.nickname != "Hacked by User A" or reloaded.nickname == original_nickname

    def test_direct_sql_respects_user_isolation(self, two_users_with_cards):
        """Direct SQL queries should filter by user_id."""
        user_a_id = two_users_with_cards["user_a_id"]
        user_b_id = two_users_with_cards["user_b_id"]

        with get_cursor(commit=False) as cur:
            # Query cards for user A
            cur.execute("SELECT COUNT(*) as cnt FROM cards WHERE user_id = %s", (str(user_a_id),))
            count_a = cur.fetchone()["cnt"]

            # Query cards for user B
            cur.execute("SELECT COUNT(*) as cnt FROM cards WHERE user_id = %s", (str(user_b_id),))
            count_b = cur.fetchone()["cnt"]

        assert count_a == 2
        assert count_b == 1


class TestOrphanDataPrevention:
    """Test that orphan records cannot be created."""

    def test_no_orphan_signup_bonuses_after_operations(self):
        """After add/edit/delete operations, no orphan signup_bonuses should exist."""
        auth = AuthService()
        email = f"orphan_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add cards with signup bonuses
        for i in range(3):
            signup_bonus = SignupBonus(
                points_or_cash=f"{(i+1)*10000} points",
                spend_requirement=(i+1)*1000,
                time_period_days=90,
                deadline=date(2026, 6, 1)
            )
            card = add_card_helper(storage, "chase_sapphire_preferred", signup_bonus=signup_bonus)
            if i == 1:
                storage.delete_card(card.id)

        # Check for orphan signup bonuses globally
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM signup_bonuses sb
                LEFT JOIN cards c ON sb.card_id = c.id
                WHERE c.id IS NULL
            """)
            orphan_count = cur.fetchone()["cnt"]

        assert orphan_count == 0, f"Found {orphan_count} orphan signup_bonuses"

    def test_no_orphan_cards_after_user_operations(self):
        """All cards should have valid user_id."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM cards c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE u.id IS NULL
            """)
            orphan_count = cur.fetchone()["cnt"]

        assert orphan_count == 0, f"Found {orphan_count} orphan cards"


class TestDataConsistency:
    """Test data remains consistent through operations."""

    def test_card_data_matches_after_reload(self):
        """Card data should be identical after save/reload cycle."""
        auth = AuthService()
        email = f"consistency_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Create card with all fields populated
        signup_bonus = SignupBonus(
            points_or_cash="80000 points",
            spend_requirement=4000,
            time_period_days=90,
            deadline=date(2026, 7, 15)
        )
        card = add_card_helper(
            storage,
            "chase_sapphire_preferred",
            opened_date=date(2026, 1, 15),
            signup_bonus=signup_bonus
        )

        # Modify card
        card.nickname = "Test Consistency Card"
        card.notes = "These are test notes.\nWith multiple lines."
        card.annual_fee = 550
        card.sub_spend_progress = 2500.0
        storage.save_card(card)

        # Reload and verify
        reloaded = storage.get_all_cards()[0]

        assert reloaded.nickname == "Test Consistency Card"
        assert reloaded.notes == "These are test notes.\nWith multiple lines."
        assert reloaded.annual_fee == 550
        assert reloaded.sub_spend_progress == 2500.0
        assert reloaded.signup_bonus is not None
        assert reloaded.signup_bonus.spend_requirement == 4000

    def test_multiple_save_reload_cycles(self):
        """Data should remain consistent through multiple save/reload cycles."""
        auth = AuthService()
        email = f"multi_cycle_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        card = add_card_helper(storage, "amex_gold")

        for i in range(5):
            card.nickname = f"Cycle {i}"
            card.notes = f"Notes for cycle {i}"
            storage.save_card(card)

            # Reload
            cards = storage.get_all_cards()
            card = cards[0]

            assert card.nickname == f"Cycle {i}"
            assert card.notes == f"Notes for cycle {i}"


class TestRefreshDuringSubmit:
    """Test data integrity when operations are interrupted (Issue #39)."""

    def test_successful_card_add_persists_to_storage(self):
        """If card add operation completes, card should be in storage."""
        auth = AuthService()
        email = f"persist_add_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add a card
        card = add_card_helper(storage, "chase_sapphire_preferred", opened_date=date(2024, 1, 15))
        card_id = card.id

        # Immediately read - should return the card
        cards = storage.get_all_cards()
        assert len(cards) == 1
        assert cards[0].id == card_id
        assert cards[0].name == "Chase Sapphire Preferred Credit Card"

    def test_failed_card_add_leaves_no_partial_data(self):
        """If storage raises error mid-save, no partial data should remain."""
        from unittest.mock import patch, MagicMock
        import psycopg2

        auth = AuthService()
        email = f"fail_add_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Count cards before
        initial_count = len(storage.get_all_cards())

        # Mock get_cursor to fail during card insertion
        with patch('src.core.db_storage.get_cursor') as mock_cursor:
            # Create a mock context manager that raises on commit
            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=MagicMock())
            mock_context.__exit__ = MagicMock(side_effect=psycopg2.OperationalError("Connection lost during save"))
            mock_cursor.return_value = mock_context

            template = get_template("chase_sapphire_preferred")

            # Attempt to add card - should raise
            with pytest.raises(psycopg2.OperationalError):
                storage.add_card_from_template(template, opened_date=date(2024, 1, 15))

        # Verify no card was added
        cards_after = storage.get_all_cards()
        assert len(cards_after) == initial_count

    def test_add_then_immediate_read_returns_card(self):
        """Adding a card then immediately reading should return the card (no stale cache)."""
        auth = AuthService()
        email = f"immediate_read_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add card
        card = add_card_helper(storage, "amex_gold", opened_date=date(2024, 1, 15))
        card_id = card.id

        # Immediately read without any delay
        retrieved_card = storage.get_card(card_id)

        assert retrieved_card is not None
        assert retrieved_card.id == card_id
        assert retrieved_card.name == "American Express Gold"

    def test_update_then_immediate_read_shows_changes(self):
        """Updating a card then immediately reading should show the changes."""
        auth = AuthService()
        email = f"update_read_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add card
        card = add_card_helper(storage, "chase_sapphire_preferred")

        # Update card
        card.nickname = "My Favorite Card"
        card.notes = "Updated notes"
        storage.save_card(card)

        # Immediately read
        retrieved_card = storage.get_card(card.id)

        assert retrieved_card.nickname == "My Favorite Card"
        assert retrieved_card.notes == "Updated notes"

    def test_delete_then_immediate_read_returns_none(self):
        """Deleting a card then immediately reading should return None."""
        auth = AuthService()
        email = f"delete_read_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add card
        card = add_card_helper(storage, "capital_one_venture_x")
        card_id = card.id

        # Verify it exists
        assert storage.get_card(card_id) is not None

        # Delete card
        deleted = storage.delete_card(card_id)
        assert deleted is True

        # Immediately read - should return None
        retrieved_card = storage.get_card(card_id)
        assert retrieved_card is None

    def test_concurrent_reads_during_write(self):
        """Multiple read operations during a write should not cause issues."""
        auth = AuthService()
        email = f"concurrent_read_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add initial cards
        card1 = add_card_helper(storage, "chase_sapphire_preferred")
        card2 = add_card_helper(storage, "amex_gold")

        # Perform multiple reads
        for _ in range(10):
            cards = storage.get_all_cards()
            assert len(cards) == 2

        # Update one card
        card1.nickname = "Updated Card 1"
        storage.save_card(card1)

        # Perform more reads
        for _ in range(10):
            cards = storage.get_all_cards()
            assert len(cards) == 2
            updated_card = next(c for c in cards if c.id == card1.id)
            assert updated_card.nickname == "Updated Card 1"

    def test_interrupted_save_preserves_original_data(self):
        """If save is interrupted, original data should be preserved."""
        from unittest.mock import patch
        import psycopg2

        auth = AuthService()
        email = f"interrupt_save_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add card with original data
        card = add_card_helper(storage, "chase_sapphire_preferred")
        card.nickname = "Original Nickname"
        storage.save_card(card)

        # Verify original data
        retrieved = storage.get_card(card.id)
        assert retrieved.nickname == "Original Nickname"

        # Attempt to update with simulated failure
        card.nickname = "Failed Update"

        with patch('src.core.db_storage.get_cursor') as mock_cursor:
            mock_cursor.side_effect = psycopg2.OperationalError("Save interrupted")

            with pytest.raises(psycopg2.OperationalError):
                storage.save_card(card)

        # Verify original data is preserved
        retrieved = storage.get_card(card.id)
        assert retrieved.nickname == "Original Nickname"

    def test_multiple_rapid_updates_stay_consistent(self):
        """Multiple rapid updates should all persist correctly."""
        auth = AuthService()
        email = f"rapid_updates_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add card
        card = add_card_helper(storage, "amex_gold")

        # Perform rapid updates (reduced to 5 for speed)
        for i in range(5):
            card.nickname = f"Update {i}"
            storage.save_card(card)

            # Verify immediately after each save
            retrieved = storage.get_card(card.id)
            assert retrieved.nickname == f"Update {i}"

        # Final verification
        final_card = storage.get_card(card.id)
        assert final_card.nickname == "Update 4"

    def test_add_multiple_cards_rapid_succession(self):
        """Adding multiple cards rapidly should all persist correctly."""
        auth = AuthService()
        email = f"rapid_adds_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        card_ids = []

        # Add multiple cards rapidly
        templates = ["chase_sapphire_preferred", "amex_gold", "capital_one_venture_x", "chase_freedom_unlimited", "citi_double_cash"]

        for template_id in templates:
            card = add_card_helper(storage, template_id)
            card_ids.append(card.id)

        # Verify all cards exist
        cards = storage.get_all_cards()
        assert len(cards) == 5

        # Verify each card can be retrieved individually
        for card_id in card_ids:
            card = storage.get_card(card_id)
            assert card is not None
            assert card.id == card_id

    def test_complex_operation_atomicity(self):
        """Complex operations should be atomic - all succeed or all fail."""
        from unittest.mock import patch
        import psycopg2

        auth = AuthService()
        email = f"atomic_op_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add a card with signup bonus
        signup_bonus = SignupBonus(
            points_or_cash="60000 points",
            spend_requirement=4000,
            time_period_days=90,
            deadline=date(2026, 6, 1)
        )
        card = add_card_helper(storage, "chase_sapphire_preferred", signup_bonus=signup_bonus)

        # Verify card and signup bonus exist
        retrieved = storage.get_card(card.id)
        assert retrieved.signup_bonus is not None
        assert retrieved.signup_bonus.points_or_cash == "60000 points"

        # Count signup bonuses in database
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM signup_bonuses WHERE card_id = %s", (card.id,))
            bonus_count_before = cur.fetchone()["cnt"]

        assert bonus_count_before == 1

        # Update card with modified signup bonus
        card.signup_bonus.spend_requirement = 5000

        # Mock a failure during save
        call_count = {"value": 0}

        def fail_on_second_query(*args, **kwargs):
            from src.core.database import get_cursor as real_get_cursor
            cursor_context = real_get_cursor(*args, **kwargs)

            # Wrap the cursor to count execute calls
            original_cursor = cursor_context.__enter__()

            class CountingCursor:
                def __getattr__(self, name):
                    return getattr(original_cursor, name)

                def execute(self, *args, **kwargs):
                    call_count["value"] += 1
                    # Fail after several successful queries (simulating partial update)
                    if call_count["value"] > 5:
                        raise psycopg2.OperationalError("Simulated failure during complex operation")
                    return original_cursor.execute(*args, **kwargs)

            class WrappedContext:
                def __enter__(self):
                    return CountingCursor()

                def __exit__(self, *args):
                    return cursor_context.__exit__(*args)

            return WrappedContext()

        with patch('src.core.db_storage.get_cursor', side_effect=fail_on_second_query):
            with pytest.raises(psycopg2.OperationalError):
                storage.save_card(card)

        # Verify original data is intact (no partial update)
        retrieved = storage.get_card(card.id)
        assert retrieved.signup_bonus.spend_requirement == 4000  # Original value

        # Verify no orphan or duplicate signup bonuses
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM signup_bonuses WHERE card_id = %s", (card.id,))
            bonus_count_after = cur.fetchone()["cnt"]

        assert bonus_count_after == 1  # Still just one bonus

    def test_read_your_own_writes_consistency(self):
        """After writing, immediate reads should reflect the write (read-your-own-writes)."""
        auth = AuthService()
        email = f"ryow_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Write: Add card
        card = add_card_helper(storage, "chase_sapphire_preferred")
        card_id = card.id

        # Read: Should see the card immediately
        cards = storage.get_all_cards()
        assert any(c.id == card_id for c in cards)

        # Write: Update card
        card.nickname = "RYOW Test Card"
        storage.save_card(card)

        # Read: Should see the update immediately
        retrieved = storage.get_card(card_id)
        assert retrieved.nickname == "RYOW Test Card"

        # Write: Delete card
        storage.delete_card(card_id)

        # Read: Should not see the card
        retrieved = storage.get_card(card_id)
        assert retrieved is None
