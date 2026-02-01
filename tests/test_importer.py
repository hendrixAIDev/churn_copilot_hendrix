"""Tests for spreadsheet importer."""

import pytest
from datetime import date, timedelta
from src.core.importer import import_from_csv, SpreadsheetImporter, ParsedCard


class TestImporter:
    """Test spreadsheet import functionality."""

    @pytest.mark.skip(reason="Requires Anthropic API credits")
    def test_parse_mixed_language_format(self):
        """Test parsing spreadsheet with mixed English/Chinese."""
        csv_content = """账户名\tStatus\tFee\t开户时间\tBonus\tTODO
Chase Sapphire Preferred\tLong-term\t$95/year\t03/18/2023\t60k points for $4000 in 3 months\tTODO: $50 hotel credit: 2027
Amex Platinum\tShort-term\t$695/year\t12/10/2024\t80k for $8000 within 6 months\tTODO: $50 Saks: 2026 H2"""

        parsed_cards, errors = import_from_csv(csv_content, skip_closed=True)

        assert len(errors) == 0
        assert len(parsed_cards) == 2

        # Check first card
        assert "Chase" in parsed_cards[0].card_name or "Sapphire" in parsed_cards[0].card_name
        assert parsed_cards[0].annual_fee == 95
        assert parsed_cards[0].opened_date == date(2023, 3, 18)

    @pytest.mark.skip(reason="Requires Anthropic API credits")
    def test_skip_closed_cards(self):
        """Test that closed cards are skipped."""
        csv_content = """Card Name\tStatus\tFee
Active Card\tLong-term\t$95
Closed Card\tClosed\t$450"""

        parsed_cards, errors = import_from_csv(csv_content, skip_closed=True)

        assert len(parsed_cards) == 1
        assert "Closed" not in parsed_cards[0].card_name

    @pytest.mark.skip(reason="Requires Anthropic API credits")
    def test_parse_benefits_with_periods(self):
        """Test benefit parsing with different periods."""
        csv_content = """Card\tFee\tTODO
Test Card\t$450\tTODO:\n* $50 Benefit: 2026 Q1 Q2 Q3 Q4\n* $200 Annual: 2026"""

        parsed_cards, errors = import_from_csv(csv_content, skip_closed=True)

        assert len(parsed_cards) == 1
        card = parsed_cards[0]

        # Should have extracted benefits
        assert len(card.benefits) >= 1

    @pytest.mark.skip(reason="Requires Anthropic API credits")
    def test_parse_sub_details(self):
        """Test SUB parsing."""
        csv_content = """Card\tBonus\tOpened
Test Card\t80k points for $8000 within 6 months\t01/01/2024"""

        parsed_cards, errors = import_from_csv(csv_content, skip_closed=True)

        assert len(parsed_cards) == 1
        card = parsed_cards[0]

        assert card.sub_reward is not None
        assert "80k" in card.sub_reward or "80,000" in card.sub_reward
        assert card.sub_spend_requirement == 8000
        assert card.sub_time_period_days == 180  # 6 months

    def test_empty_spreadsheet(self):
        """Test handling of empty spreadsheet."""
        csv_content = """Card Name\tFee\tStatus"""

        parsed_cards, errors = import_from_csv(csv_content, skip_closed=True)

        # Should handle gracefully
        assert isinstance(parsed_cards, list)


class TestDeadlineCalculations:
    """Test automatic deadline calculation features."""

    def test_calculate_deadline_from_opened_date(self):
        """Test auto-calculation of SUB deadline from opened_date."""
        card = ParsedCard(
            card_name="Test Card",
            opened_date=date(2024, 1, 1),
            sub_time_period_days=90,
            sub_reward="60k points"
        )

        deadline = card.calculate_deadline()
        assert deadline == date(2024, 3, 31)  # Jan 1 + 90 days = March 31

    def test_calculate_deadline_preserves_existing(self):
        """Test that existing deadline is preserved."""
        existing_deadline = date(2024, 6, 1)
        card = ParsedCard(
            card_name="Test Card",
            opened_date=date(2024, 1, 1),
            sub_time_period_days=90,
            sub_deadline=existing_deadline,
            sub_reward="60k points"
        )

        deadline = card.calculate_deadline()
        assert deadline == existing_deadline

    def test_calculate_deadline_missing_data(self):
        """Test deadline calculation with missing data."""
        # Missing opened_date
        card1 = ParsedCard(
            card_name="Test Card",
            sub_time_period_days=90,
            sub_reward="60k points"
        )
        assert card1.calculate_deadline() is None

        # Missing time_period_days
        card2 = ParsedCard(
            card_name="Test Card",
            opened_date=date(2024, 1, 1),
            sub_reward="60k points"
        )
        assert card2.calculate_deadline() is None

    def test_get_days_remaining(self):
        """Test calculation of days remaining until deadline."""
        today = date(2024, 6, 1)
        card = ParsedCard(
            card_name="Test Card",
            opened_date=date(2024, 3, 1),
            sub_time_period_days=90,
            sub_reward="60k points"
        )

        # Calculate from specific reference date
        days_remaining = card.get_days_remaining(reference_date=today)
        expected_deadline = date(2024, 5, 30)  # 90 days from March 1
        expected_days = (expected_deadline - today).days
        assert days_remaining == expected_days

    def test_get_days_remaining_expired(self):
        """Test days remaining for expired deadline."""
        today = date(2024, 6, 1)
        card = ParsedCard(
            card_name="Test Card",
            opened_date=date(2024, 1, 1),
            sub_time_period_days=90,  # Deadline was April 1
            sub_reward="60k points"
        )

        days_remaining = card.get_days_remaining(reference_date=today)
        assert days_remaining < 0  # Should be negative

    def test_calculate_annual_fee_date(self):
        """Test calculation of annual fee date."""
        card = ParsedCard(
            card_name="Test Card",
            opened_date=date(2024, 3, 15),
            annual_fee=95
        )

        annual_fee_date = card.calculate_annual_fee_date()
        assert annual_fee_date == date(2025, 3, 15)

    def test_calculate_annual_fee_date_no_opened_date(self):
        """Test annual fee date calculation without opened_date."""
        card = ParsedCard(
            card_name="Test Card",
            annual_fee=95
        )

        annual_fee_date = card.calculate_annual_fee_date()
        assert annual_fee_date is None

    def test_normalize_auto_calculates_deadline(self):
        """Test that normalize() auto-calculates deadline."""
        card = ParsedCard(
            card_name="Test Card",
            opened_date=date(2024, 1, 1),
            sub_time_period_days=90,
            sub_reward="60k points"
        )

        # Before normalization, sub_deadline should be None
        assert card.sub_deadline is None

        # After normalization, it should be calculated
        card.normalize()
        assert card.sub_deadline == date(2024, 3, 31)

    def test_normalize_with_messy_data(self):
        """Test normalization with various edge cases."""
        card = ParsedCard(
            card_name="  Test Card  ",  # Extra spaces
            annual_fee=-50,  # Negative fee
            sub_achieved=None,  # None instead of False
            opened_date=date(2024, 1, 1),
            sub_time_period_days=180
        )

        card.normalize()

        assert card.card_name == "Test Card"  # Stripped
        assert card.annual_fee == 0.0  # Converted to 0
        assert card.sub_achieved is False  # None -> False
        assert card.sub_deadline == date(2024, 6, 29)  # Auto-calculated

    @pytest.mark.skip(reason="Requires Anthropic API credits")
    def test_full_import_with_deadline_calculation(self):
        """Test end-to-end import with automatic deadline calculation."""
        csv_content = """Card\tOpened\tBonus\tStatus
Chase Sapphire Preferred\t01/01/2024\t60k points for $4000 in 3 months\tActive"""

        parsed_cards, errors = import_from_csv(csv_content, skip_closed=True)

        assert len(errors) == 0
        assert len(parsed_cards) == 1

        card = parsed_cards[0]
        assert card.opened_date == date(2024, 1, 1)
        assert card.sub_time_period_days == 90  # 3 months

        # Should have auto-calculated deadline (after normalization)
        # The deadline is set during normalize() which is called in parse_spreadsheet
        deadline = card.calculate_deadline()
        assert deadline is not None
        # Verify deadline is calculated (AI may return slightly different date based on interpretation)
        # The important thing is that it's automatically calculated
        assert deadline >= date(2024, 3, 31) and deadline <= date(2024, 4, 1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
