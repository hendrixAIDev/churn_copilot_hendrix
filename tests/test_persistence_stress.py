"""Stress tests for data persistence."""

import pytest
from uuid import uuid4
from datetime import datetime, date
import os

# Ensure DATABASE_URL is set for tests
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/churnpilot")

from src.core.db_storage import DatabaseStorage
from src.core.auth import AuthService
from src.core.models import SignupBonus
from src.core.database import get_cursor, check_connection
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
    """Verify database is accessible for stress tests."""

    def test_database_is_connected(self):
        """Database should be reachable."""
        assert check_connection() is True


class TestRapidOperations:
    """Test rapid save/load doesn't lose data."""

    @pytest.fixture
    def user_storage(self):
        """Create test user and storage."""
        auth = AuthService()
        email = f"stress_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        return DatabaseStorage(user.id)

    def test_rapid_card_adds(self, user_storage):
        """Adding 20 cards rapidly should not lose any."""
        for i in range(20):
            add_card_helper(user_storage, "chase_sapphire_preferred")

        cards = user_storage.get_all_cards()
        assert len(cards) == 20

    def test_rapid_edits_same_card(self, user_storage):
        """Editing same card 50 times should persist last value."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")

        for i in range(50):
            card.nickname = f"Nickname {i}"
            user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.nickname == "Nickname 49"

    def test_concurrent_operations(self, user_storage):
        """Interleaved add/edit/delete should be consistent."""
        # Add 5 cards
        cards = []
        for i in range(5):
            card = add_card_helper(user_storage, "chase_sapphire_preferred")
            cards.append(card)

        # Edit card 0, delete card 1, add new card
        cards[0].nickname = "Edited"
        user_storage.save_card(cards[0])
        user_storage.delete_card(cards[1].id)
        add_card_helper(user_storage, "amex_platinum")

        result = user_storage.get_all_cards()
        assert len(result) == 5
        nicknames = [c.nickname for c in result]
        assert "Edited" in nicknames

    def test_rapid_signup_bonus_updates(self, user_storage):
        """Updating signup bonus progress 30 times should persist last value."""
        signup_bonus = SignupBonus(
            points_or_cash="60000 points",
            spend_requirement=4000,
            time_period_days=90,
            deadline=date(2026, 6, 1)
        )
        card = add_card_helper(
            user_storage,
            "chase_sapphire_preferred",
            signup_bonus=signup_bonus
        )

        for i in range(30):
            card.sub_spend_progress = float(i * 100)
            user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.sub_spend_progress == 2900.0

    def test_alternating_add_delete(self, user_storage):
        """Adding then deleting 10 cards should leave 0."""
        for i in range(10):
            card = add_card_helper(user_storage, "chase_sapphire_preferred")
            user_storage.delete_card(card.id)

        cards = user_storage.get_all_cards()
        assert len(cards) == 0

    def test_bulk_add_then_bulk_delete(self, user_storage):
        """Adding 15 cards then deleting all should leave 0."""
        cards = []
        for i in range(15):
            card = add_card_helper(user_storage, "chase_sapphire_preferred")
            cards.append(card)

        for card in cards:
            user_storage.delete_card(card.id)

        remaining = user_storage.get_all_cards()
        assert len(remaining) == 0


class TestSessionPersistence:
    """Test data persists across multiple storage instances."""

    def test_cards_persist_new_storage_instance(self):
        """Cards should be visible with new storage instance after adds."""
        auth = AuthService()
        email = f"session_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")

        # First session - add cards
        storage1 = DatabaseStorage(user.id)
        for i in range(5):
            add_card_helper(storage1, "chase_sapphire_preferred")

        # Second session - verify
        storage2 = DatabaseStorage(user.id)
        cards = storage2.get_all_cards()
        assert len(cards) == 5

    def test_edits_persist_new_storage_instance(self):
        """Card edits should be visible with new storage instance."""
        auth = AuthService()
        email = f"edit_session_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")

        # First session - add and edit
        storage1 = DatabaseStorage(user.id)
        card = add_card_helper(storage1, "chase_sapphire_preferred")
        card.nickname = "My Edited Card"
        card.notes = "Important notes here"
        storage1.save_card(card)

        # Second session - verify edits
        storage2 = DatabaseStorage(user.id)
        cards = storage2.get_all_cards()
        assert len(cards) == 1
        assert cards[0].nickname == "My Edited Card"
        assert cards[0].notes == "Important notes here"

    def test_deletes_persist_new_storage_instance(self):
        """Deletions should persist across storage instances."""
        auth = AuthService()
        email = f"delete_session_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")

        # First session - add cards
        storage1 = DatabaseStorage(user.id)
        card1 = add_card_helper(storage1, "chase_sapphire_preferred")
        card2 = add_card_helper(storage1, "amex_gold")

        # Delete one
        storage1.delete_card(card1.id)

        # Second session - verify deletion persisted
        storage2 = DatabaseStorage(user.id)
        cards = storage2.get_all_cards()
        assert len(cards) == 1
        assert cards[0].id == card2.id


class TestMultipleUsersStress:
    """Test multiple users don't interfere with each other."""

    def test_ten_users_independent_cards(self):
        """10 users adding cards simultaneously should not interfere."""
        auth = AuthService()
        user_storages = []

        # Create 10 users
        for i in range(10):
            email = f"multi_user_{i}_{datetime.now().timestamp()}@test.com"
            user = auth.register(email, "TestPassword123!")
            storage = DatabaseStorage(user.id)
            user_storages.append(storage)

        # Each user adds different number of cards
        for i, storage in enumerate(user_storages):
            for j in range(i + 1):  # User 0 adds 1 card, user 1 adds 2, etc.
                add_card_helper(storage, "chase_sapphire_preferred")

        # Verify each user sees only their cards
        for i, storage in enumerate(user_storages):
            cards = storage.get_all_cards()
            expected_count = i + 1
            assert len(cards) == expected_count, f"User {i} expected {expected_count} cards, got {len(cards)}"

    def test_user_edit_doesnt_affect_others(self):
        """Editing user A's card should not affect user B's cards."""
        auth = AuthService()

        # Create two users
        user_a = auth.register(f"user_a_{datetime.now().timestamp()}@test.com", "TestPassword123!")
        user_b = auth.register(f"user_b_{datetime.now().timestamp()}@test.com", "TestPassword123!")

        storage_a = DatabaseStorage(user_a.id)
        storage_b = DatabaseStorage(user_b.id)

        # Both add cards
        card_a = add_card_helper(storage_a, "chase_sapphire_preferred")
        card_b = add_card_helper(storage_b, "chase_sapphire_preferred")

        # User A edits their card
        card_a.nickname = "A's Card"
        storage_a.save_card(card_a)

        # User B's card should be unchanged
        cards_b = storage_b.get_all_cards()
        assert cards_b[0].nickname != "A's Card"

    def test_user_delete_doesnt_affect_others(self):
        """Deleting user A's card should not affect user B's cards."""
        auth = AuthService()

        user_a = auth.register(f"del_a_{datetime.now().timestamp()}@test.com", "TestPassword123!")
        user_b = auth.register(f"del_b_{datetime.now().timestamp()}@test.com", "TestPassword123!")

        storage_a = DatabaseStorage(user_a.id)
        storage_b = DatabaseStorage(user_b.id)

        # Both add cards
        card_a = add_card_helper(storage_a, "chase_sapphire_preferred")
        card_b = add_card_helper(storage_b, "chase_sapphire_preferred")

        # User A deletes their card
        storage_a.delete_card(card_a.id)

        # User B's card should still exist
        cards_b = storage_b.get_all_cards()
        assert len(cards_b) == 1
        assert cards_b[0].id == card_b.id
