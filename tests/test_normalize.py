"""Unit tests for card name and issuer normalization.

Run with: pytest tests/test_normalize.py -v
"""

import pytest
from src.core.normalize import (
    normalize_issuer,
    simplify_card_name,
    match_to_library_template,
    get_display_name,
)


class TestNormalizeIssuer:
    """Tests for issuer normalization."""

    def test_amex_variations(self):
        """Test American Express normalization."""
        assert normalize_issuer("AMEX") == "American Express"
        assert normalize_issuer("amex") == "American Express"
        assert normalize_issuer("American Express") == "American Express"
        assert normalize_issuer("americanexpress") == "American Express"

    def test_chase_variations(self):
        """Test Chase normalization."""
        assert normalize_issuer("Chase") == "Chase"
        assert normalize_issuer("chase") == "Chase"
        assert normalize_issuer("Chase Bank") == "Chase"
        assert normalize_issuer("JPMorgan Chase") == "Chase"

    def test_capital_one_variations(self):
        """Test Capital One normalization."""
        assert normalize_issuer("Capital One") == "Capital One"
        assert normalize_issuer("CapitalOne") == "Capital One"
        assert normalize_issuer("cap one") == "Capital One"

    def test_citi_variations(self):
        """Test Citi normalization."""
        assert normalize_issuer("Citi") == "Citi"
        assert normalize_issuer("Citibank") == "Citi"
        assert normalize_issuer("citigroup") == "Citi"

    def test_other_issuers(self):
        """Test other issuer normalizations."""
        assert normalize_issuer("US Bank") == "US Bank"
        assert normalize_issuer("usbank") == "US Bank"
        assert normalize_issuer("Bank of America") == "Bank of America"
        assert normalize_issuer("bofa") == "Bank of America"
        assert normalize_issuer("bilt rewards") == "Bilt"

    def test_unknown_issuer(self):
        """Test that unknown issuers are preserved."""
        assert normalize_issuer("New Issuer Inc") == "New Issuer Inc"

    def test_empty_issuer(self):
        """Test empty issuer handling."""
        assert normalize_issuer("") == ""
        assert normalize_issuer(None) is None


class TestSimplifyCardName:
    """Tests for card name simplification."""

    def test_chase_sapphire_preferred(self):
        """Test Chase Sapphire Preferred simplification."""
        result = simplify_card_name("Chase Sapphire Preferred Credit Card", "Chase")
        assert result == "Sapphire Preferred"

    def test_amex_platinum(self):
        """Test Amex Platinum variations."""
        result = simplify_card_name("The Platinum Card from American Express", "American Express")
        assert result == "Platinum"

        result = simplify_card_name("American Express Platinum", "American Express")
        assert result == "Platinum"

    def test_capital_one_venture_x(self):
        """Test Capital One Venture X."""
        result = simplify_card_name("Capital One Venture X", "Capital One")
        assert result == "Venture X"

    def test_removes_credit_card_suffix(self):
        """Test removal of 'Credit Card' suffix."""
        result = simplify_card_name("Some Card Credit Card", None)
        assert "Credit Card" not in result
        assert "credit card" not in result.lower()

    def test_removes_registered_trademark(self):
        """Test removal of trademark symbols."""
        result = simplify_card_name("Platinum Card®", None)
        assert "®" not in result

    def test_preserves_core_name(self):
        """Test that core card name is preserved."""
        result = simplify_card_name("Sapphire Preferred", "Chase")
        assert result == "Sapphire Preferred"

    def test_empty_name(self):
        """Test empty name handling."""
        assert simplify_card_name("", None) == ""

    def test_issuer_only_name_preserved(self):
        """Test that if only issuer is in name, original is kept."""
        # If simplification would result in empty, keep original
        result = simplify_card_name("Chase Card", "Chase")
        # Should not be empty
        assert result != ""


class TestMatchToLibraryTemplate:
    """Tests for matching cards to library templates."""

    def test_exact_match(self):
        """Test exact name match."""
        result = match_to_library_template("American Express Platinum", "American Express")
        assert result == "amex_platinum"

    def test_variation_match(self):
        """Test matching with name variation."""
        result = match_to_library_template(
            "The Platinum Card from American Express",
            "American Express"
        )
        assert result == "amex_platinum"

    def test_chase_sapphire_reserve(self):
        """Test Chase Sapphire Reserve matching."""
        result = match_to_library_template("Chase Sapphire Reserve", "Chase")
        assert result == "chase_sapphire_reserve"

    def test_no_match(self):
        """Test card that doesn't match any template."""
        result = match_to_library_template("Unknown Card", "Unknown Bank")
        assert result is None

    def test_wrong_issuer_no_match(self):
        """Test that wrong issuer doesn't match."""
        # Platinum is Amex, not Chase
        result = match_to_library_template("Platinum", "Chase")
        assert result != "amex_platinum"


class TestGetDisplayName:
    """Tests for get_display_name function."""

    def test_basic_display_name(self):
        """Test basic display name generation."""
        result = get_display_name("Chase Sapphire Preferred Credit Card", "Chase")
        assert result == "Sapphire Preferred"

    def test_display_name_preserves_core(self):
        """Test that core name is preserved."""
        result = get_display_name("Venture X", "Capital One")
        assert result == "Venture X"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
