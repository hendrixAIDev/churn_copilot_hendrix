"""Unit tests for period utilities and benefit tracking.

Run with: pytest tests/test_periods.py -v
"""

import pytest
from datetime import date

from src.core.models import Credit, CreditUsage
from src.core.periods import (
    get_current_period,
    get_period_display_name,
    is_credit_used_this_period,
    is_reminder_snoozed,
    get_unused_credits_count,
    mark_credit_used,
    mark_credit_unused,
    snooze_credit_reminder,
    unsnooze_credit_reminder,
    snooze_all_reminders,
)


class TestGetCurrentPeriod:
    """Tests for get_current_period function."""

    def test_monthly_period(self):
        """Test monthly period calculation."""
        assert get_current_period("monthly", date(2024, 1, 15)) == "2024-01"
        assert get_current_period("monthly", date(2024, 12, 1)) == "2024-12"
        assert get_current_period("monthly", date(2025, 6, 30)) == "2025-06"

    def test_quarterly_period(self):
        """Test quarterly period calculation."""
        assert get_current_period("quarterly", date(2024, 1, 15)) == "2024-Q1"
        assert get_current_period("quarterly", date(2024, 3, 31)) == "2024-Q1"
        assert get_current_period("quarterly", date(2024, 4, 1)) == "2024-Q2"
        assert get_current_period("quarterly", date(2024, 6, 30)) == "2024-Q2"
        assert get_current_period("quarterly", date(2024, 7, 1)) == "2024-Q3"
        assert get_current_period("quarterly", date(2024, 10, 15)) == "2024-Q4"
        assert get_current_period("quarterly", date(2024, 12, 31)) == "2024-Q4"

    def test_semi_annual_period(self):
        """Test semi-annual period calculation."""
        assert get_current_period("semi-annually", date(2024, 1, 1)) == "2024-H1"
        assert get_current_period("semi-annually", date(2024, 6, 30)) == "2024-H1"
        assert get_current_period("semi-annually", date(2024, 7, 1)) == "2024-H2"
        assert get_current_period("semi-annually", date(2024, 12, 31)) == "2024-H2"
        # Also test "semi-annual" variant
        assert get_current_period("semi-annual", date(2024, 3, 15)) == "2024-H1"

    def test_annual_period(self):
        """Test annual period calculation."""
        assert get_current_period("annual", date(2024, 1, 1)) == "2024"
        assert get_current_period("annual", date(2024, 12, 31)) == "2024"
        assert get_current_period("annually", date(2025, 6, 15)) == "2025"

    def test_unknown_frequency(self):
        """Test that unknown frequencies default to annual."""
        assert get_current_period("unknown", date(2024, 6, 15)) == "2024"


class TestGetPeriodDisplayName:
    """Tests for get_period_display_name function."""

    def test_monthly_display(self):
        """Test monthly period display name."""
        assert get_period_display_name("monthly", date(2024, 1, 15)) == "January 2024"
        assert get_period_display_name("monthly", date(2024, 12, 1)) == "December 2024"

    def test_quarterly_display(self):
        """Test quarterly period display name."""
        assert get_period_display_name("quarterly", date(2024, 2, 15)) == "Q1 2024"
        assert get_period_display_name("quarterly", date(2024, 5, 15)) == "Q2 2024"

    def test_semi_annual_display(self):
        """Test semi-annual period display name."""
        assert get_period_display_name("semi-annually", date(2024, 3, 15)) == "H1 2024"
        assert get_period_display_name("semi-annually", date(2024, 9, 15)) == "H2 2024"

    def test_annual_display(self):
        """Test annual period display name."""
        assert get_period_display_name("annual", date(2024, 6, 15)) == "2024"


class TestIsCreditUsedThisPeriod:
    """Tests for is_credit_used_this_period function."""

    def test_credit_not_in_usage(self):
        """Test when credit has no usage data."""
        credit_usage = {}
        assert is_credit_used_this_period("Uber Credit", "monthly", credit_usage, date(2024, 1, 15)) is False

    def test_credit_used_current_period(self):
        """Test when credit was used in current period."""
        credit_usage = {
            "Uber Credit": CreditUsage(last_used_period="2024-01")
        }
        assert is_credit_used_this_period("Uber Credit", "monthly", credit_usage, date(2024, 1, 15)) is True

    def test_credit_used_different_period(self):
        """Test when credit was used in a different period."""
        credit_usage = {
            "Uber Credit": CreditUsage(last_used_period="2024-01")
        }
        # New month - credit not used yet
        assert is_credit_used_this_period("Uber Credit", "monthly", credit_usage, date(2024, 2, 15)) is False

    def test_quarterly_credit(self):
        """Test quarterly credit usage tracking."""
        credit_usage = {
            "Saks Credit": CreditUsage(last_used_period="2024-Q1")
        }
        # Same quarter
        assert is_credit_used_this_period("Saks Credit", "quarterly", credit_usage, date(2024, 3, 15)) is True
        # New quarter
        assert is_credit_used_this_period("Saks Credit", "quarterly", credit_usage, date(2024, 4, 1)) is False


class TestIsReminderSnoozed:
    """Tests for is_reminder_snoozed function."""

    def test_no_usage_data(self):
        """Test when credit has no usage data."""
        credit_usage = {}
        assert is_reminder_snoozed("Uber Credit", credit_usage, date(2024, 1, 15)) is False

    def test_no_snooze_set(self):
        """Test when snooze is not set."""
        credit_usage = {
            "Uber Credit": CreditUsage(last_used_period="2024-01")
        }
        assert is_reminder_snoozed("Uber Credit", credit_usage, date(2024, 1, 15)) is False

    def test_snoozed_until_future(self):
        """Test when reminder is snoozed until future date."""
        credit_usage = {
            "Uber Credit": CreditUsage(reminder_snoozed_until=date(2024, 2, 1))
        }
        assert is_reminder_snoozed("Uber Credit", credit_usage, date(2024, 1, 15)) is True

    def test_snooze_expired(self):
        """Test when snooze has expired."""
        credit_usage = {
            "Uber Credit": CreditUsage(reminder_snoozed_until=date(2024, 1, 1))
        }
        assert is_reminder_snoozed("Uber Credit", credit_usage, date(2024, 1, 15)) is False


class TestGetUnusedCreditsCount:
    """Tests for get_unused_credits_count function."""

    @pytest.fixture
    def sample_credits(self):
        """Create sample credits for testing."""
        return [
            Credit(name="Uber Credit", amount=15.0, frequency="monthly"),
            Credit(name="Saks Credit", amount=50.0, frequency="semi-annually"),
            Credit(name="Airline Credit", amount=200.0, frequency="annual"),
        ]

    def test_all_unused(self, sample_credits):
        """Test when all credits are unused."""
        credit_usage = {}
        count = get_unused_credits_count(sample_credits, credit_usage, date(2024, 1, 15))
        assert count == 3

    def test_some_used(self, sample_credits):
        """Test when some credits are used."""
        credit_usage = {
            "Uber Credit": CreditUsage(last_used_period="2024-01")
        }
        count = get_unused_credits_count(sample_credits, credit_usage, date(2024, 1, 15))
        assert count == 2

    def test_all_used(self, sample_credits):
        """Test when all credits are used."""
        credit_usage = {
            "Uber Credit": CreditUsage(last_used_period="2024-01"),
            "Saks Credit": CreditUsage(last_used_period="2024-H1"),
            "Airline Credit": CreditUsage(last_used_period="2024"),
        }
        count = get_unused_credits_count(sample_credits, credit_usage, date(2024, 1, 15))
        assert count == 0

    def test_excludes_snoozed(self, sample_credits):
        """Test that snoozed credits are not counted."""
        credit_usage = {
            "Uber Credit": CreditUsage(reminder_snoozed_until=date(2024, 2, 1))
        }
        count = get_unused_credits_count(sample_credits, credit_usage, date(2024, 1, 15))
        assert count == 2  # Uber is snoozed, so only 2 counted

    def test_includes_snoozed_when_requested(self, sample_credits):
        """Test including snoozed credits when requested."""
        credit_usage = {
            "Uber Credit": CreditUsage(reminder_snoozed_until=date(2024, 2, 1))
        }
        count = get_unused_credits_count(sample_credits, credit_usage, date(2024, 1, 15), include_snoozed=True)
        assert count == 3


class TestMarkCreditUsed:
    """Tests for mark_credit_used function."""

    def test_mark_new_credit(self):
        """Test marking a credit that has no usage data."""
        credit_usage = {}
        result = mark_credit_used("Uber Credit", "monthly", credit_usage, date(2024, 1, 15))

        assert "Uber Credit" in result
        assert result["Uber Credit"].last_used_period == "2024-01"

    def test_mark_existing_credit(self):
        """Test marking a credit that already has usage data."""
        credit_usage = {
            "Uber Credit": CreditUsage(last_used_period="2023-12")
        }
        result = mark_credit_used("Uber Credit", "monthly", credit_usage, date(2024, 1, 15))

        assert result["Uber Credit"].last_used_period == "2024-01"


class TestMarkCreditUnused:
    """Tests for mark_credit_unused function."""

    def test_mark_unused(self):
        """Test marking a credit as unused."""
        credit_usage = {
            "Uber Credit": CreditUsage(last_used_period="2024-01")
        }
        result = mark_credit_unused("Uber Credit", credit_usage)

        assert result["Uber Credit"].last_used_period is None

    def test_mark_nonexistent_credit(self):
        """Test marking a credit that doesn't exist in usage."""
        credit_usage = {}
        result = mark_credit_unused("Uber Credit", credit_usage)

        # Should not raise, just return unchanged
        assert "Uber Credit" not in result


class TestSnoozeCredits:
    """Tests for snooze/unsnooze functions."""

    def test_snooze_credit(self):
        """Test snoozing a credit reminder."""
        credit_usage = {}
        result = snooze_credit_reminder("Uber Credit", credit_usage, date(2024, 2, 1))

        assert "Uber Credit" in result
        assert result["Uber Credit"].reminder_snoozed_until == date(2024, 2, 1)

    def test_unsnooze_credit(self):
        """Test unsnoozing a credit reminder."""
        credit_usage = {
            "Uber Credit": CreditUsage(reminder_snoozed_until=date(2024, 2, 1))
        }
        result = unsnooze_credit_reminder("Uber Credit", credit_usage)

        assert result["Uber Credit"].reminder_snoozed_until is None

    def test_snooze_all(self):
        """Test snoozing all credit reminders."""
        credits = [
            Credit(name="Uber Credit", amount=15.0, frequency="monthly"),
            Credit(name="Saks Credit", amount=50.0, frequency="semi-annually"),
        ]
        credit_usage = {}
        result = snooze_all_reminders(credits, credit_usage, date(2024, 2, 1))

        assert result["Uber Credit"].reminder_snoozed_until == date(2024, 2, 1)
        assert result["Saks Credit"].reminder_snoozed_until == date(2024, 2, 1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
