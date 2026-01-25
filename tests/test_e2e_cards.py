"""E2E tests for card management using database backend."""

import pytest
from datetime import datetime, date
from uuid import UUID
import os

# Ensure DATABASE_URL is set for tests
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/churnpilot")

from src.core.auth import AuthService
from src.core.db_storage import DatabaseStorage
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
    """Verify database is accessible for card tests."""

    def test_database_is_connected(self):
        """Database should be reachable."""
        assert check_connection() is True


class TestAddCard:
    """Test adding cards via DatabaseStorage."""

    @pytest.fixture
    def user_storage(self):
        """Create test user and return storage instance."""
        auth = AuthService()
        email = f"card_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        return DatabaseStorage(user.id)

    def test_add_card_from_template(self, user_storage):
        """Should add card from template successfully."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")

        assert card is not None
        assert card.name is not None
        assert card.issuer is not None

    def test_add_card_appears_in_list(self, user_storage):
        """Added card should appear in get_all_cards."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")

        cards = user_storage.get_all_cards()
        card_ids = [c.id for c in cards]

        assert card.id in card_ids

    def test_add_card_persists_in_database(self, user_storage):
        """Added card should be stored in database."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")

        with get_cursor(commit=False) as cur:
            cur.execute("SELECT name, issuer FROM cards WHERE id = %s", (card.id,))
            row = cur.fetchone()

        assert row is not None
        assert row["name"] is not None

    def test_add_card_with_signup_bonus(self, user_storage):
        """Card with signup bonus should store bonus data."""
        signup_bonus = SignupBonus(
            points_or_cash="60000 points",
            spend_requirement=4000,
            time_period_days=90,
            deadline=date(2026, 4, 1)
        )

        card = add_card_helper(
            user_storage,
            "chase_sapphire_preferred",
            signup_bonus=signup_bonus
        )

        # Reload card
        cards = user_storage.get_all_cards()
        reloaded = next(c for c in cards if c.id == card.id)

        assert reloaded.signup_bonus is not None
        assert reloaded.signup_bonus.spend_requirement == 4000

    def test_add_multiple_cards(self, user_storage):
        """Should be able to add multiple cards."""
        add_card_helper(user_storage, "chase_sapphire_preferred")
        add_card_helper(user_storage, "amex_gold")
        add_card_helper(user_storage, "chase_freedom_unlimited")

        cards = user_storage.get_all_cards()
        assert len(cards) == 3


class TestEditCard:
    """Test editing cards via DatabaseStorage."""

    @pytest.fixture
    def user_storage_with_card(self):
        """Create test user with one card."""
        auth = AuthService()
        email = f"edit_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        card = add_card_helper(storage, "chase_sapphire_preferred")

        return {"storage": storage, "card": card}

    def test_edit_card_nickname(self, user_storage_with_card):
        """Should be able to change card nickname."""
        storage = user_storage_with_card["storage"]
        card = user_storage_with_card["card"]

        card.nickname = "My Primary Card"
        storage.save_card(card)

        # Reload
        cards = storage.get_all_cards()
        reloaded = next(c for c in cards if c.id == card.id)

        assert reloaded.nickname == "My Primary Card"

    def test_edit_card_notes(self, user_storage_with_card):
        """Should be able to change card notes."""
        storage = user_storage_with_card["storage"]
        card = user_storage_with_card["card"]

        card.notes = "This is my favorite travel card.\nGreat for dining."
        storage.save_card(card)

        cards = storage.get_all_cards()
        reloaded = next(c for c in cards if c.id == card.id)

        assert "favorite travel card" in reloaded.notes
        assert "\n" in reloaded.notes

    def test_edit_card_annual_fee(self, user_storage_with_card):
        """Should be able to update annual fee."""
        storage = user_storage_with_card["storage"]
        card = user_storage_with_card["card"]

        card.annual_fee = 550
        storage.save_card(card)

        cards = storage.get_all_cards()
        reloaded = next(c for c in cards if c.id == card.id)

        assert reloaded.annual_fee == 550

    def test_edit_card_closed_date(self, user_storage_with_card):
        """Should be able to close a card."""
        storage = user_storage_with_card["storage"]
        card = user_storage_with_card["card"]

        card.closed_date = date.today()
        storage.save_card(card)

        cards = storage.get_all_cards()
        reloaded = next(c for c in cards if c.id == card.id)

        assert reloaded.closed_date == date.today()

    def test_edit_multiple_fields_at_once(self, user_storage_with_card):
        """Should be able to edit multiple fields in one save."""
        storage = user_storage_with_card["storage"]
        card = user_storage_with_card["card"]

        card.nickname = "Updated Card"
        card.notes = "Updated notes"
        card.annual_fee = 250
        storage.save_card(card)

        cards = storage.get_all_cards()
        reloaded = next(c for c in cards if c.id == card.id)

        assert reloaded.nickname == "Updated Card"
        assert reloaded.notes == "Updated notes"
        assert reloaded.annual_fee == 250


class TestUpdateSignupBonus:
    """Test updating signup bonus progress."""

    @pytest.fixture
    def user_storage_with_sub_card(self):
        """Create test user with card that has signup bonus."""
        auth = AuthService()
        email = f"sub_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        signup_bonus = SignupBonus(
            points_or_cash="60000 points",
            spend_requirement=4000,
            time_period_days=90,
            deadline=date(2026, 6, 1)
        )

        card = add_card_helper(
            storage,
            "chase_sapphire_preferred",
            signup_bonus=signup_bonus
        )

        return {"storage": storage, "card": card}

    def test_update_sub_progress(self, user_storage_with_sub_card):
        """Should be able to update spend progress."""
        storage = user_storage_with_sub_card["storage"]
        card = user_storage_with_sub_card["card"]

        card.sub_spend_progress = 2500.0
        storage.save_card(card)

        cards = storage.get_all_cards()
        reloaded = next(c for c in cards if c.id == card.id)

        assert reloaded.sub_spend_progress == 2500.0

    def test_mark_sub_achieved(self, user_storage_with_sub_card):
        """Should be able to mark SUB as achieved."""
        storage = user_storage_with_sub_card["storage"]
        card = user_storage_with_sub_card["card"]

        card.sub_spend_progress = 4000.0
        card.sub_achieved = True
        storage.save_card(card)

        cards = storage.get_all_cards()
        reloaded = next(c for c in cards if c.id == card.id)

        assert reloaded.sub_achieved is True


class TestDeleteCard:
    """Test deleting cards via DatabaseStorage."""

    @pytest.fixture
    def user_storage_with_cards(self):
        """Create test user with multiple cards."""
        auth = AuthService()
        email = f"delete_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        cards = []
        for template_id in ["chase_sapphire_preferred", "amex_gold"]:
            card = add_card_helper(storage, template_id)
            cards.append(card)

        return {"storage": storage, "cards": cards, "user_id": user.id}

    def test_delete_card_removes_from_list(self, user_storage_with_cards):
        """Deleted card should not appear in list."""
        storage = user_storage_with_cards["storage"]
        cards = user_storage_with_cards["cards"]

        card_to_delete = cards[0]
        storage.delete_card(card_to_delete.id)

        remaining = storage.get_all_cards()
        remaining_ids = [c.id for c in remaining]

        assert card_to_delete.id not in remaining_ids
        assert len(remaining) == 1

    def test_delete_card_removes_from_database(self, user_storage_with_cards):
        """Deleted card should be removed from database."""
        storage = user_storage_with_cards["storage"]
        cards = user_storage_with_cards["cards"]

        card_to_delete = cards[0]
        storage.delete_card(card_to_delete.id)

        with get_cursor(commit=False) as cur:
            cur.execute("SELECT id FROM cards WHERE id = %s", (card_to_delete.id,))
            row = cur.fetchone()

        assert row is None

    def test_delete_card_cascades_signup_bonus(self, user_storage_with_cards):
        """Deleting card should also delete its signup bonus."""
        storage = user_storage_with_cards["storage"]

        # Add card with signup bonus
        signup_bonus = SignupBonus(
            points_or_cash="100000 points",
            spend_requirement=6000,
            time_period_days=90,
            deadline=date(2026, 6, 1)
        )
        card = add_card_helper(
            storage,
            "chase_sapphire_preferred",
            signup_bonus=signup_bonus
        )

        # Verify signup bonus exists
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT card_id FROM signup_bonuses WHERE card_id = %s", (card.id,))
            assert cur.fetchone() is not None

        # Delete card
        storage.delete_card(card.id)

        # Verify signup bonus is also deleted
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT card_id FROM signup_bonuses WHERE card_id = %s", (card.id,))
            assert cur.fetchone() is None

    def test_delete_nonexistent_card(self, user_storage_with_cards):
        """Deleting nonexistent card should not raise error."""
        storage = user_storage_with_cards["storage"]

        # Use a valid UUID format that doesn't exist
        import uuid
        nonexistent_id = str(uuid.uuid4())
        # This should not raise
        storage.delete_card(nonexistent_id)


class TestCardPersistenceAcrossSessions:
    """Test cards persist across storage sessions."""

    def test_cards_persist_across_storage_instances(self):
        """Cards should be visible with new storage instance."""
        auth = AuthService()
        email = f"persist_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")

        # First session - add cards
        storage1 = DatabaseStorage(user.id)
        add_card_helper(storage1, "chase_sapphire_preferred")
        add_card_helper(storage1, "amex_gold")

        # Second session - verify cards exist
        storage2 = DatabaseStorage(user.id)
        cards = storage2.get_all_cards()

        assert len(cards) == 2

    def test_edits_persist_across_storage_instances(self):
        """Card edits should be visible with new storage instance."""
        auth = AuthService()
        email = f"edit_persist_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")

        # First session - add and edit card
        storage1 = DatabaseStorage(user.id)
        card = add_card_helper(storage1, "chase_sapphire_preferred")
        card.nickname = "My CSP"
        storage1.save_card(card)

        # Second session - verify edit persisted
        storage2 = DatabaseStorage(user.id)
        cards = storage2.get_all_cards()
        reloaded = next(c for c in cards if c.id == card.id)

        assert reloaded.nickname == "My CSP"


class TestUserIsolation:
    """Test that users cannot see each other's cards."""

    def test_user_only_sees_own_cards(self):
        """User A should not see User B's cards."""
        auth = AuthService()

        # Create user A with 2 cards
        user_a = auth.register(
            f"user_a_{datetime.now().timestamp()}@test.com",
            "TestPassword123!"
        )
        storage_a = DatabaseStorage(user_a.id)
        add_card_helper(storage_a, "chase_sapphire_preferred")
        add_card_helper(storage_a, "amex_gold")

        # Create user B with 3 cards
        user_b = auth.register(
            f"user_b_{datetime.now().timestamp()}@test.com",
            "TestPassword123!"
        )
        storage_b = DatabaseStorage(user_b.id)
        add_card_helper(storage_b, "chase_freedom_unlimited")
        add_card_helper(storage_b, "capital_one_venture_x")
        add_card_helper(storage_b, "amex_platinum")

        # Verify user A only sees their cards
        cards_a = storage_a.get_all_cards()
        assert len(cards_a) == 2

        # Verify user B only sees their cards
        cards_b = storage_b.get_all_cards()
        assert len(cards_b) == 3

        # Verify no overlap in card IDs
        ids_a = {c.id for c in cards_a}
        ids_b = {c.id for c in cards_b}
        assert len(ids_a & ids_b) == 0
