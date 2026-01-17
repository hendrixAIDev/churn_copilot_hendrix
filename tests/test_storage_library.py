"""Unit tests for CardStorage.add_card_from_template and Card nickname field.

Run with: pytest tests/test_storage_library.py -v
"""

import pytest
import tempfile
import shutil
from datetime import date
from pathlib import Path

from src.core.storage import CardStorage
from src.core.models import Card, SignupBonus, Credit, CreditUsage
from src.core.library import CardTemplate, get_template
from src.core.periods import mark_credit_used


class TestCardNickname:
    """Tests for Card model nickname field."""

    def test_card_with_nickname(self):
        """Test creating a Card with a nickname."""
        card = Card(
            id="test-123",
            name="Test Card",
            nickname="My Test Card",
            issuer="Test Bank",
            annual_fee=100,
        )

        assert card.nickname == "My Test Card"

    def test_card_without_nickname(self):
        """Test creating a Card without nickname defaults to None."""
        card = Card(
            id="test-123",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=100,
        )

        assert card.nickname is None

    def test_card_nickname_empty_string(self):
        """Test that empty string nickname is allowed."""
        card = Card(
            id="test-123",
            name="Test Card",
            nickname="",
            issuer="Test Bank",
            annual_fee=100,
        )

        assert card.nickname == ""

    def test_card_serialization_with_nickname(self):
        """Test that nickname is included in serialization."""
        card = Card(
            id="test-123",
            name="Test Card",
            nickname="P2's Card",
            issuer="Test Bank",
            annual_fee=100,
        )

        data = card.model_dump()
        assert "nickname" in data
        assert data["nickname"] == "P2's Card"

    def test_card_deserialization_with_nickname(self):
        """Test that nickname is restored from dict."""
        data = {
            "id": "test-123",
            "name": "Test Card",
            "nickname": "Restored Nickname",
            "issuer": "Test Bank",
            "annual_fee": 100,
        }

        card = Card.model_validate(data)
        assert card.nickname == "Restored Nickname"


class TestAddCardFromTemplate:
    """Tests for CardStorage.add_card_from_template method."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory for tests."""
        temp_dir = tempfile.mkdtemp()
        storage = CardStorage(data_dir=temp_dir)
        yield storage
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_template(self):
        """Create a sample template for testing."""
        return CardTemplate(
            id="test_card",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=95,
            credits=[
                Credit(name="Monthly Credit", amount=10.0, frequency="monthly"),
                Credit(name="Annual Credit", amount=100.0, frequency="annual"),
            ],
        )

    def test_add_card_from_template_basic(self, temp_storage, sample_template):
        """Test basic card creation from template."""
        card = temp_storage.add_card_from_template(template=sample_template)

        assert card.name == "Test Card"
        assert card.issuer == "Test Bank"
        assert card.annual_fee == 95
        assert len(card.credits) == 2
        assert card.id is not None  # Should have generated UUID

    def test_add_card_from_template_with_nickname(self, temp_storage, sample_template):
        """Test adding card with nickname."""
        card = temp_storage.add_card_from_template(
            template=sample_template,
            nickname="My Primary Card",
        )

        assert card.nickname == "My Primary Card"
        assert card.name == "Test Card"

    def test_add_card_from_template_without_nickname(self, temp_storage, sample_template):
        """Test adding card without nickname results in None."""
        card = temp_storage.add_card_from_template(template=sample_template)

        assert card.nickname is None

    def test_add_card_from_template_with_opened_date(self, temp_storage, sample_template):
        """Test adding card with opened date."""
        opened = date(2024, 1, 15)
        card = temp_storage.add_card_from_template(
            template=sample_template,
            opened_date=opened,
        )

        assert card.opened_date == opened

    def test_add_card_from_template_with_signup_bonus(self, temp_storage, sample_template):
        """Test adding card with signup bonus."""
        sub = SignupBonus(
            points_or_cash="80,000 points",
            spend_requirement=6000.0,
            time_period_days=90,
        )
        card = temp_storage.add_card_from_template(
            template=sample_template,
            signup_bonus=sub,
        )

        assert card.signup_bonus is not None
        assert card.signup_bonus.points_or_cash == "80,000 points"
        assert card.signup_bonus.spend_requirement == 6000.0

    def test_add_card_from_template_all_fields(self, temp_storage, sample_template):
        """Test adding card with all optional fields."""
        sub = SignupBonus(
            points_or_cash="50,000 points",
            spend_requirement=4000.0,
            time_period_days=90,
        )
        opened = date(2024, 6, 1)

        card = temp_storage.add_card_from_template(
            template=sample_template,
            nickname="Work Card",
            opened_date=opened,
            signup_bonus=sub,
        )

        assert card.nickname == "Work Card"
        assert card.opened_date == opened
        assert card.signup_bonus.points_or_cash == "50,000 points"
        assert card.name == "Test Card"
        assert len(card.credits) == 2

    def test_add_card_from_template_persists(self, temp_storage, sample_template):
        """Test that added card is persisted to storage."""
        card = temp_storage.add_card_from_template(
            template=sample_template,
            nickname="Persisted Card",
        )

        # Retrieve from storage
        all_cards = temp_storage.get_all_cards()
        assert len(all_cards) == 1
        assert all_cards[0].id == card.id
        assert all_cards[0].nickname == "Persisted Card"

    def test_add_card_from_template_generates_unique_ids(self, temp_storage, sample_template):
        """Test that each added card gets a unique ID."""
        card1 = temp_storage.add_card_from_template(template=sample_template)
        card2 = temp_storage.add_card_from_template(template=sample_template)

        assert card1.id != card2.id

    def test_add_card_from_template_credits_copied(self, temp_storage, sample_template):
        """Test that template credits are properly copied to card."""
        card = temp_storage.add_card_from_template(template=sample_template)

        assert len(card.credits) == 2
        credit_names = [c.name for c in card.credits]
        assert "Monthly Credit" in credit_names
        assert "Annual Credit" in credit_names

    def test_add_card_from_amex_platinum_template(self, temp_storage):
        """Test adding card from real Amex Platinum template."""
        template = get_template("amex_platinum")
        assert template is not None

        card = temp_storage.add_card_from_template(
            template=template,
            nickname="P1 Plat",
            opened_date=date(2024, 3, 15),
        )

        assert "Platinum" in card.name
        assert card.issuer == "American Express"
        assert card.annual_fee >= 695  # May vary (currently $895)
        assert card.nickname == "P1 Plat"
        assert len(card.credits) >= 5  # Should have many credits


class TestStorageWithNickname:
    """Test storage operations with nickname field."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory for tests."""
        temp_dir = tempfile.mkdtemp()
        storage = CardStorage(data_dir=temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_nickname_survives_storage_roundtrip(self, temp_storage):
        """Test that nickname is preserved through save/load cycle."""
        template = CardTemplate(
            id="test",
            name="Test",
            issuer="Bank",
            annual_fee=0,
        )

        card = temp_storage.add_card_from_template(
            template=template,
            nickname="Special Name",
        )

        # Create new storage instance pointing to same directory
        new_storage = CardStorage(data_dir=temp_storage.data_dir)
        loaded_cards = new_storage.get_all_cards()

        assert len(loaded_cards) == 1
        assert loaded_cards[0].nickname == "Special Name"

    def test_get_card_returns_nickname(self, temp_storage):
        """Test that get_card returns card with nickname."""
        template = CardTemplate(
            id="test",
            name="Test",
            issuer="Bank",
            annual_fee=0,
        )

        card = temp_storage.add_card_from_template(
            template=template,
            nickname="Retrievable",
        )

        retrieved = temp_storage.get_card(card.id)
        assert retrieved is not None
        assert retrieved.nickname == "Retrievable"


class TestSubProgress:
    """Tests for SUB progress tracking fields."""

    def test_card_sub_progress_default(self):
        """Test that sub_spend_progress defaults to None."""
        card = Card(
            id="test-123",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=100,
        )

        assert card.sub_spend_progress is None
        assert card.sub_achieved is False

    def test_card_with_sub_progress(self):
        """Test creating a Card with SUB progress tracking."""
        card = Card(
            id="test-123",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=100,
            signup_bonus=SignupBonus(
                points_or_cash="80,000 points",
                spend_requirement=6000.0,
                time_period_days=90,
            ),
            sub_spend_progress=2500.0,
            sub_achieved=False,
        )

        assert card.sub_spend_progress == 2500.0
        assert card.sub_achieved is False

    def test_card_sub_achieved(self):
        """Test marking SUB as achieved."""
        card = Card(
            id="test-123",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=100,
            signup_bonus=SignupBonus(
                points_or_cash="80,000 points",
                spend_requirement=6000.0,
                time_period_days=90,
            ),
            sub_spend_progress=6500.0,
            sub_achieved=True,
        )

        assert card.sub_achieved is True
        assert card.sub_spend_progress == 6500.0

    def test_sub_progress_serialization(self):
        """Test that SUB progress fields are properly serialized."""
        card = Card(
            id="test-123",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=100,
            sub_spend_progress=1234.56,
            sub_achieved=True,
        )

        # Serialize and deserialize
        card_dict = card.model_dump()
        assert card_dict["sub_spend_progress"] == 1234.56
        assert card_dict["sub_achieved"] is True

        # Recreate from dict
        restored = Card(**card_dict)
        assert restored.sub_spend_progress == 1234.56
        assert restored.sub_achieved is True


class TestCreditUsageSerialization:
    """Tests for credit_usage serialization through storage.

    These tests verify that CreditUsage objects survive the JSON save/load cycle.
    This is a regression test for the bug where CreditUsage was serialized as
    its string representation instead of a dictionary.
    """

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory for tests."""
        temp_dir = tempfile.mkdtemp()
        storage = CardStorage(data_dir=temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def card_with_credits(self, temp_storage):
        """Create a card with credits for testing."""
        template = CardTemplate(
            id="test_card",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=95,
            credits=[
                Credit(name="Monthly Credit", amount=10.0, frequency="monthly"),
                Credit(name="Annual Credit", amount=100.0, frequency="annual"),
            ],
        )
        return temp_storage.add_card_from_template(template=template)

    def test_credit_usage_survives_update_and_reload(self, temp_storage, card_with_credits):
        """Test that credit_usage is preserved through update_card and reload."""
        # Mark a credit as used
        credit_usage = mark_credit_used(
            "Monthly Credit",
            "monthly",
            {},
            date(2024, 1, 15)
        )

        # Update the card with credit_usage
        temp_storage.update_card(card_with_credits.id, {"credit_usage": credit_usage})

        # Create a new storage instance (simulates server restart)
        new_storage = CardStorage(data_dir=temp_storage.data_dir)
        loaded_card = new_storage.get_card(card_with_credits.id)

        # Verify credit_usage was preserved
        assert loaded_card is not None
        assert "Monthly Credit" in loaded_card.credit_usage
        assert loaded_card.credit_usage["Monthly Credit"].last_used_period == "2024-01"

    def test_credit_usage_with_snooze_survives_reload(self, temp_storage, card_with_credits):
        """Test that reminder_snoozed_until is preserved through save/load."""
        credit_usage = {
            "Monthly Credit": CreditUsage(
                last_used_period="2024-01",
                reminder_snoozed_until=date(2024, 2, 1)
            )
        }

        # Update and reload
        temp_storage.update_card(card_with_credits.id, {"credit_usage": credit_usage})
        new_storage = CardStorage(data_dir=temp_storage.data_dir)
        loaded_card = new_storage.get_card(card_with_credits.id)

        # Verify both fields were preserved
        assert loaded_card.credit_usage["Monthly Credit"].last_used_period == "2024-01"
        assert loaded_card.credit_usage["Monthly Credit"].reminder_snoozed_until == date(2024, 2, 1)

    def test_multiple_credits_usage_survives_reload(self, temp_storage, card_with_credits):
        """Test that multiple credit usages are all preserved."""
        credit_usage = {
            "Monthly Credit": CreditUsage(last_used_period="2024-01"),
            "Annual Credit": CreditUsage(last_used_period="2024"),
        }

        temp_storage.update_card(card_with_credits.id, {"credit_usage": credit_usage})
        new_storage = CardStorage(data_dir=temp_storage.data_dir)
        loaded_card = new_storage.get_card(card_with_credits.id)

        assert len(loaded_card.credit_usage) == 2
        assert loaded_card.credit_usage["Monthly Credit"].last_used_period == "2024-01"
        assert loaded_card.credit_usage["Annual Credit"].last_used_period == "2024"

    def test_benefits_reminder_snoozed_until_survives_reload(self, temp_storage, card_with_credits):
        """Test that card-level snooze is preserved."""
        temp_storage.update_card(
            card_with_credits.id,
            {"benefits_reminder_snoozed_until": date(2024, 3, 1)}
        )

        new_storage = CardStorage(data_dir=temp_storage.data_dir)
        loaded_card = new_storage.get_card(card_with_credits.id)

        assert loaded_card.benefits_reminder_snoozed_until == date(2024, 3, 1)

    def test_mark_used_then_unused_cycle(self, temp_storage, card_with_credits):
        """Test the full UI cycle: mark used -> reload -> mark unused -> reload.

        This is a regression test for the bug where unchecking a credit caused
        corruption because CreditUsage objects from loaded cards weren't being
        properly serialized when passed back to update_card.
        """
        from src.core.periods import mark_credit_used, mark_credit_unused

        # Step 1: Mark credit as used
        usage = mark_credit_used("Monthly Credit", "monthly", {}, date(2024, 1, 15))
        temp_storage.update_card(card_with_credits.id, {"credit_usage": usage})

        # Step 2: Reload (simulates page refresh)
        storage2 = CardStorage(data_dir=temp_storage.data_dir)
        loaded_card = storage2.get_card(card_with_credits.id)
        assert loaded_card.credit_usage["Monthly Credit"].last_used_period == "2024-01"

        # Step 3: Mark as unused (this is exactly what the UI does)
        new_usage = dict(loaded_card.credit_usage)  # UI copies like this
        new_usage = mark_credit_unused("Monthly Credit", new_usage)
        storage2.update_card(loaded_card.id, {"credit_usage": new_usage})

        # Step 4: Reload again and verify
        storage3 = CardStorage(data_dir=temp_storage.data_dir)
        final_card = storage3.get_card(card_with_credits.id)

        assert "Monthly Credit" in final_card.credit_usage
        assert final_card.credit_usage["Monthly Credit"].last_used_period is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
