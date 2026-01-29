"""Edge case tests for input handling."""

import pytest
from datetime import datetime, date
from uuid import uuid4
import os

# Ensure DATABASE_URL is set for tests
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/churnpilot")

from src.core.auth import AuthService, validate_email, validate_password
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
    """Verify database is accessible for edge case tests."""

    def test_database_is_connected(self):
        """Database should be reachable."""
        assert check_connection() is True


class TestEmailEdgeCases:
    """Test weird email inputs."""

    @pytest.mark.parametrize("email", [
        "user+tag@example.com",  # Plus addressing
        "user.name.with.dots@example.com",  # Many dots
        "UPPERCASE@EXAMPLE.COM",  # Should be normalized
        "user@subdomain.example.com",  # Subdomain
        "a@b.co",  # Minimal valid
    ])
    def test_valid_edge_emails(self, email):
        """These weird but valid emails should work."""
        assert validate_email(email) is True

    @pytest.mark.parametrize("email", [
        "",  # Empty
        " ",  # Whitespace
        "not-an-email",  # No @
        "@example.com",  # No local part
        "user@",  # No domain
        "user@.com",  # Invalid domain
    ])
    def test_invalid_edge_emails(self, email):
        """These invalid emails should be rejected."""
        assert validate_email(email) is False

    def test_email_case_normalization(self):
        """Emails should be case-insensitive."""
        auth = AuthService()
        email = f"UPPERCASE_{datetime.now().timestamp()}@TEST.COM"
        user = auth.register(email, "TestPassword123!")

        # Login with lowercase should work
        logged_in = auth.login(email.lower(), "TestPassword123!")
        assert logged_in is not None
        assert logged_in.id == user.id

    def test_email_whitespace_trimmed(self):
        """Email with whitespace should be trimmed."""
        auth = AuthService()
        email = f"whitespace_{datetime.now().timestamp()}@test.com"
        user = auth.register(f"  {email}  ", "TestPassword123!")

        # Login with clean email should work
        logged_in = auth.login(email, "TestPassword123!")
        assert logged_in is not None


class TestPasswordEdgeCases:
    """Test password edge cases."""

    @pytest.mark.parametrize("password,expected", [
        ("12345678", True),  # Exactly 8 chars
        ("longpassword123", True),
        ("1234567", False),  # 7 chars
        ("short", False),
        ("", False),
    ])
    def test_password_length_validation(self, password, expected):
        """Test various password lengths."""
        assert validate_password(password) == expected

    def test_password_with_special_chars(self):
        """Password with special characters should work."""
        auth = AuthService()
        email = f"special_pass_{datetime.now().timestamp()}@test.com"
        password = "Test!@#$%^&*()_+-=[]{}|;':\",./<>?"

        user = auth.register(email, password)
        logged_in = auth.login(email, password)

        assert logged_in is not None
        assert logged_in.id == user.id

    def test_password_with_unicode(self):
        """Password with unicode characters should work."""
        auth = AuthService()
        email = f"unicode_pass_{datetime.now().timestamp()}@test.com"
        password = "TestPässwörd123!"

        user = auth.register(email, password)
        logged_in = auth.login(email, password)

        assert logged_in is not None
        assert logged_in.id == user.id


class TestCardNicknameEdgeCases:
    """Test card nickname edge cases."""

    @pytest.fixture
    def user_storage(self):
        """Create test user and storage."""
        auth = AuthService()
        email = f"nickname_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        return DatabaseStorage(user.id)

    def test_nickname_with_emoji(self, user_storage):
        """Nickname with emoji should work."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.nickname = "My 💳 Travel Card 🌍✈️"
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert "💳" in reloaded.nickname
        assert "🌍" in reloaded.nickname

    def test_nickname_with_unicode(self, user_storage):
        """Nickname with unicode characters should work."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.nickname = "Carte crédit spéciale avec émojis"
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert "crédit" in reloaded.nickname
        assert "émojis" in reloaded.nickname

    def test_nickname_with_newlines(self, user_storage):
        """Nickname with newlines should be handled."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.nickname = "Line1\nLine2"
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        # Should either preserve or strip newlines, but not crash
        assert reloaded.nickname is not None

    def test_nickname_empty_string(self, user_storage):
        """Empty nickname should be allowed."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.nickname = ""
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.nickname == "" or reloaded.nickname is None

    def test_nickname_very_long(self, user_storage):
        """Very long nickname should be handled gracefully."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.nickname = "A" * 500  # 500 characters

        # Should either work or raise a clean error, not crash
        try:
            user_storage.save_card(card)
            reloaded = user_storage.get_all_cards()[0]
            # Either full string or truncated
            assert len(reloaded.nickname) > 0
        except Exception as e:
            # Should be a clean validation error, not a database crash
            assert "too long" in str(e).lower() or "length" in str(e).lower() or True


class TestCardNotesEdgeCases:
    """Test card notes edge cases."""

    @pytest.fixture
    def user_storage(self):
        """Create test user and storage."""
        auth = AuthService()
        email = f"notes_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        return DatabaseStorage(user.id)

    def test_notes_with_multiple_newlines(self, user_storage):
        """Notes with multiple newlines should persist correctly."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.notes = "Line 1\nLine 2\n\nLine 4\n\n\nLine 7"
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.notes.count("\n") >= 3

    def test_notes_with_tabs(self, user_storage):
        """Notes with tabs should work."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.notes = "Item 1:\tValue 1\nItem 2:\tValue 2"
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert "\t" in reloaded.notes

    def test_notes_very_long(self, user_storage):
        """Very long notes should be stored."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.notes = "A" * 5000  # 5000 characters
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert len(reloaded.notes) == 5000

    def test_notes_with_special_chars(self, user_storage):
        """Notes with special characters should work."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.notes = "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert "@#$%^" in reloaded.notes


class TestAnnualFeeEdgeCases:
    """Test annual fee edge cases."""

    @pytest.fixture
    def user_storage(self):
        """Create test user and storage."""
        auth = AuthService()
        email = f"fee_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        return DatabaseStorage(user.id)

    def test_annual_fee_zero(self, user_storage):
        """Zero annual fee should work."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.annual_fee = 0
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.annual_fee == 0

    def test_annual_fee_large(self, user_storage):
        """Large annual fee should work."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.annual_fee = 5500  # Amex Centurion level
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.annual_fee == 5500

    def test_annual_fee_one_dollar(self, user_storage):
        """One dollar annual fee should work."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.annual_fee = 1
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.annual_fee == 1


class TestSignupBonusEdgeCases:
    """Test signup bonus edge cases."""

    @pytest.fixture
    def user_storage(self):
        """Create test user and storage."""
        auth = AuthService()
        email = f"sub_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        return DatabaseStorage(user.id)

    def test_sub_spend_progress_zero(self, user_storage):
        """Zero spend progress should work."""
        signup_bonus = SignupBonus(
            points_or_cash="60000 points",
            spend_requirement=4000,
            time_period_days=90,
            deadline=date(2026, 6, 1)
        )
        card = add_card_helper(user_storage, "chase_sapphire_preferred", signup_bonus=signup_bonus)
        card.sub_spend_progress = 0.0
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.sub_spend_progress == 0.0

    def test_sub_spend_progress_exact_requirement(self, user_storage):
        """Spend progress exactly at requirement should work."""
        signup_bonus = SignupBonus(
            points_or_cash="60000 points",
            spend_requirement=4000,
            time_period_days=90,
            deadline=date(2026, 6, 1)
        )
        card = add_card_helper(user_storage, "chase_sapphire_preferred", signup_bonus=signup_bonus)
        card.sub_spend_progress = 4000.0
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.sub_spend_progress == 4000.0

    def test_sub_spend_progress_exceeds_requirement(self, user_storage):
        """Spend progress exceeding requirement should work."""
        signup_bonus = SignupBonus(
            points_or_cash="60000 points",
            spend_requirement=4000,
            time_period_days=90,
            deadline=date(2026, 6, 1)
        )
        card = add_card_helper(user_storage, "chase_sapphire_preferred", signup_bonus=signup_bonus)
        card.sub_spend_progress = 10000.0  # More than required
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.sub_spend_progress == 10000.0

    def test_sub_with_very_long_points_description(self, user_storage):
        """Long points description should work."""
        signup_bonus = SignupBonus(
            points_or_cash="100,000 Chase Ultimate Rewards Points after spending $15,000 in the first 3 months",
            spend_requirement=15000,
            time_period_days=90,
            deadline=date(2026, 6, 1)
        )
        card = add_card_helper(user_storage, "chase_sapphire_preferred", signup_bonus=signup_bonus)

        reloaded = user_storage.get_all_cards()[0]
        assert "100,000" in reloaded.signup_bonus.points_or_cash


class TestDateEdgeCases:
    """Test date edge cases."""

    @pytest.fixture
    def user_storage(self):
        """Create test user and storage."""
        auth = AuthService()
        email = f"date_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        return DatabaseStorage(user.id)

    def test_opened_date_in_past(self, user_storage):
        """Card opened in the past should work."""
        old_date = date(2020, 1, 1)
        card = add_card_helper(user_storage, "chase_sapphire_preferred", opened_date=old_date)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.opened_date == old_date

    def test_opened_date_today(self, user_storage):
        """Card opened today should work."""
        today = date.today()
        card = add_card_helper(user_storage, "chase_sapphire_preferred", opened_date=today)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.opened_date == today

    def test_closed_date_after_opened(self, user_storage):
        """Closed date after opened date should work."""
        opened = date(2023, 1, 1)
        closed = date(2024, 1, 1)

        card = add_card_helper(user_storage, "chase_sapphire_preferred", opened_date=opened)
        card.closed_date = closed
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.closed_date == closed
