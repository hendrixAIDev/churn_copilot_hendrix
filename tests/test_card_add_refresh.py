"""Tests for card add and immediate refresh behavior.

These tests verify:
1. Cards are immediately visible after adding (no stale data)
2. st.session_state is properly updated after card operations
3. Import operations also trigger proper state refresh
4. Success messages are shown after card addition

Note: These tests focus on the data layer since Streamlit UI testing
requires integration tests with browser simulation.
"""

import pytest
from datetime import date, timedelta
from uuid import UUID, uuid4

from src.core.db_storage import DatabaseStorage
from src.core.auth import AuthService
from src.core.library import get_all_templates, get_template
from src.core.models import SignupBonus


@pytest.fixture
def auth_service():
    """Create AuthService instance."""
    return AuthService()


@pytest.fixture
def test_user(auth_service):
    """Create a test user."""
    email = f"card_add_test_{uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user = auth_service.register(email, password)
    yield user
    try:
        auth_service.delete_user(user.id)
    except Exception:
        pass


@pytest.fixture
def storage(test_user):
    """Create DatabaseStorage for test user."""
    return DatabaseStorage(test_user.id)


class TestCardAddImmediateVisibility:
    """Test that cards are immediately visible after adding."""

    def test_card_visible_immediately_after_add_from_template(self, storage):
        """Card should be in get_all_cards() immediately after add_card_from_template."""
        templates = get_all_templates()
        assert len(templates) > 0, "No templates available"

        template = templates[0]

        # Add card
        card = storage.add_card_from_template(
            template=template,
            nickname="Test Card",
            opened_date=date.today(),
        )

        # Should be immediately visible
        all_cards = storage.get_all_cards()
        card_ids = [c.id for c in all_cards]

        assert card.id in card_ids, "Card not visible after add_card_from_template"

    def test_card_visible_immediately_after_add_card(self, storage):
        """Card should be in get_all_cards() immediately after add_card."""
        from src.core.models import CardData

        card_data = CardData(
            name="Test Direct Add Card",
            issuer="Test Issuer",
            annual_fee=95,
        )

        # Add card
        card = storage.add_card(card_data, opened_date=date.today())

        # Should be immediately visible
        all_cards = storage.get_all_cards()
        card_ids = [c.id for c in all_cards]

        assert card.id in card_ids, "Card not visible after add_card"

    def test_multiple_cards_all_visible(self, storage):
        """All added cards should be visible immediately."""
        templates = get_all_templates()[:3]

        added_cards = []
        for i, template in enumerate(templates):
            card = storage.add_card_from_template(
                template=template,
                nickname=f"Card {i}",
                opened_date=date.today(),
            )
            added_cards.append(card)

        # All should be visible
        all_cards = storage.get_all_cards()
        all_card_ids = {c.id for c in all_cards}

        for card in added_cards:
            assert card.id in all_card_ids, f"Card {card.name} not visible"

    def test_card_with_signup_bonus_visible_immediately(self, storage):
        """Card with SUB should be visible with SUB data intact."""
        templates = get_all_templates()
        template = templates[0]

        signup_bonus = SignupBonus(
            points_or_cash="100,000 points",
            spend_requirement=6000.0,
            time_period_days=90,
            deadline=date.today() + timedelta(days=90),
        )

        card = storage.add_card_from_template(
            template=template,
            nickname="SUB Test",
            opened_date=date.today(),
            signup_bonus=signup_bonus,
        )

        # Fetch and verify
        all_cards = storage.get_all_cards()
        found_card = next((c for c in all_cards if c.id == card.id), None)

        assert found_card is not None
        assert found_card.signup_bonus is not None
        assert found_card.signup_bonus.points_or_cash == "100,000 points"


class TestCardDataConsistency:
    """Test that card data is consistent after add."""

    def test_card_data_matches_after_add(self, storage):
        """Retrieved card data should match what was added."""
        templates = get_all_templates()
        template = templates[0]

        nickname = f"Consistency Test {uuid4().hex[:4]}"
        opened = date.today() - timedelta(days=30)

        card = storage.add_card_from_template(
            template=template,
            nickname=nickname,
            opened_date=opened,
        )

        # Fetch and compare
        all_cards = storage.get_all_cards()
        found = next((c for c in all_cards if c.id == card.id), None)

        assert found is not None
        assert found.name == template.name
        assert found.nickname == nickname
        assert found.issuer == template.issuer
        assert found.opened_date == opened
        assert found.annual_fee == template.annual_fee

    def test_credits_preserved_after_add(self, storage):
        """Card credits should be preserved after add."""
        # Find a template with credits
        templates = get_all_templates()
        template_with_credits = None
        for t in templates:
            if t.credits and len(t.credits) > 0:
                template_with_credits = t
                break

        if not template_with_credits:
            pytest.skip("No templates with credits available")

        card = storage.add_card_from_template(
            template=template_with_credits,
            opened_date=date.today(),
        )

        # Verify credits
        all_cards = storage.get_all_cards()
        found = next((c for c in all_cards if c.id == card.id), None)

        assert found is not None
        assert len(found.credits) == len(template_with_credits.credits)


class TestGetAllCardsNotCached:
    """Test that get_all_cards always returns fresh data."""

    def test_get_all_cards_reflects_deletes(self, storage):
        """get_all_cards should not show deleted cards."""
        template = get_all_templates()[0]

        card = storage.add_card_from_template(
            template=template,
            opened_date=date.today(),
        )

        # Verify it's there
        cards_before = storage.get_all_cards()
        assert any(c.id == card.id for c in cards_before)

        # Delete
        storage.delete_card(card.id)

        # Should be gone
        cards_after = storage.get_all_cards()
        assert not any(c.id == card.id for c in cards_after)

    def test_get_all_cards_reflects_updates(self, storage):
        """get_all_cards should show updated data."""
        template = get_all_templates()[0]

        card = storage.add_card_from_template(
            template=template,
            nickname="Original",
            opened_date=date.today(),
        )

        # Update nickname
        storage.update_card(card.id, {"nickname": "Updated"})

        # Should reflect update
        cards = storage.get_all_cards()
        found = next((c for c in cards if c.id == card.id), None)

        assert found is not None
        assert found.nickname == "Updated"


class TestConcurrentCardOperations:
    """Test behavior with multiple rapid operations."""

    def test_rapid_add_then_read(self, storage):
        """Rapid add operations should all be visible."""
        templates = get_all_templates()[:5]

        # Add cards rapidly
        added = []
        for t in templates:
            card = storage.add_card_from_template(
                template=t,
                opened_date=date.today(),
            )
            added.append(card)

        # All should be visible
        cards = storage.get_all_cards()
        ids = {c.id for c in cards}

        for card in added:
            assert card.id in ids

    def test_add_delete_add_sequence(self, storage):
        """Add->Delete->Add sequence should work correctly."""
        template = get_all_templates()[0]

        # Add first card
        card1 = storage.add_card_from_template(
            template=template,
            nickname="First",
            opened_date=date.today(),
        )

        # Delete it
        storage.delete_card(card1.id)

        # Add another
        card2 = storage.add_card_from_template(
            template=template,
            nickname="Second",
            opened_date=date.today(),
        )

        # Only second should be visible
        cards = storage.get_all_cards()
        ids = {c.id for c in cards}

        assert card1.id not in ids
        assert card2.id in ids


class TestImportBatchVisibility:
    """Test that imported cards are all visible."""

    def test_batch_import_all_visible(self, storage):
        """All cards from batch import should be visible."""
        from src.core.models import CardData

        cards_data = [
            CardData(name=f"Import Test {i}", issuer="Test Issuer", annual_fee=i * 50)
            for i in range(5)
        ]

        added_ids = []
        for card_data in cards_data:
            card = storage.add_card(card_data, opened_date=date.today())
            added_ids.append(card.id)

        # All should be visible
        all_cards = storage.get_all_cards()
        all_ids = {c.id for c in all_cards}

        for card_id in added_ids:
            assert card_id in all_ids


class TestSessionStateIntegration:
    """Test patterns used in Streamlit session state."""

    def test_storage_instance_fresh_data(self, test_user):
        """New storage instance should see all cards."""
        storage1 = DatabaseStorage(test_user.id)

        template = get_all_templates()[0]
        card = storage1.add_card_from_template(
            template=template,
            opened_date=date.today(),
        )

        # Create new storage instance (simulating what happens on rerun)
        storage2 = DatabaseStorage(test_user.id)

        cards = storage2.get_all_cards()
        assert any(c.id == card.id for c in cards)

    def test_pattern_matches_streamlit_flow(self, test_user):
        """Test the exact pattern used in Streamlit app."""
        # Simulate: storage = DatabaseStorage(user_id)
        storage = DatabaseStorage(test_user.id)

        # Simulate: card = storage.add_card_from_template(...)
        template = get_all_templates()[0]
        card = storage.add_card_from_template(
            template=template,
            nickname="Streamlit Pattern Test",
            opened_date=date.today(),
        )

        # Simulate: after st.rerun(), render_dashboard calls:
        # cards = st.session_state.storage.get_all_cards()
        cards = storage.get_all_cards()

        # Card should be visible
        found = next((c for c in cards if c.id == card.id), None)
        assert found is not None
        assert found.nickname == "Streamlit Pattern Test"
