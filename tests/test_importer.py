"""Tests for spreadsheet importer."""

import pytest
from datetime import date
from src.core.importer import import_from_csv, SpreadsheetImporter


class TestImporter:
    """Test spreadsheet import functionality."""

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

    def test_skip_closed_cards(self):
        """Test that closed cards are skipped."""
        csv_content = """Card Name\tStatus\tFee
Active Card\tLong-term\t$95
Closed Card\tClosed\t$450"""

        parsed_cards, errors = import_from_csv(csv_content, skip_closed=True)

        assert len(parsed_cards) == 1
        assert "Closed" not in parsed_cards[0].card_name

    def test_parse_benefits_with_periods(self):
        """Test benefit parsing with different periods."""
        csv_content = """Card\tFee\tTODO
Test Card\t$450\tTODO:\n* $50 Benefit: 2026 Q1 Q2 Q3 Q4\n* $200 Annual: 2026"""

        parsed_cards, errors = import_from_csv(csv_content, skip_closed=True)

        assert len(parsed_cards) == 1
        card = parsed_cards[0]

        # Should have extracted benefits
        assert len(card.benefits) >= 1

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
