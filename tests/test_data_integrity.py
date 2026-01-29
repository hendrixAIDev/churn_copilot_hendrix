"""Data integrity tests."""

import pytest
from datetime import datetime, date
from uuid import uuid4
import os

# Ensure DATABASE_URL is set for tests
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/churnpilot")

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
