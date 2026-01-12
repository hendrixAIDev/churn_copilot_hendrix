"""Test case for Amex Platinum card extraction.

This test verifies the end-to-end flow using the unified pipeline:
1. Fetch card page via Jina Reader
2. Extract structured card data using Claude

Run with: pytest tests/test_amex_platinum.py -v -s
"""

import pytest
from src.core import extract_from_url, fetch_card_page
from src.core.exceptions import FetchError, ExtractionError


# Target URLs for testing
AMEX_PLATINUM_URL = "https://www.uscreditcardguide.com/amex-platinum/"

# Expected data points to verify extraction
EXPECTED_ISSUER = "American Express"
EXPECTED_CARD_NAME_CONTAINS = "Platinum"


class TestAmexPlatinumFetch:
    """Test fetching Amex Platinum card page."""

    def test_fetch_card_page(self):
        """Test that we can fetch content from a card review page."""
        content = fetch_card_page(AMEX_PLATINUM_URL)

        # Should have substantial content
        assert len(content) > 1000, f"Content too short: {len(content)} chars"

        # Should contain benefit-related keywords
        content_lower = content.lower()
        assert any(
            keyword in content_lower
            for keyword in ["credit", "benefit", "platinum", "annual fee"]
        ), "Content missing expected keywords"

        print(f"\nOK - Fetched {len(content):,} characters")


class TestAmexPlatinumExtraction:
    """Test full extraction pipeline for Amex Platinum."""

    def test_extract_amex_platinum(self):
        """Test end-to-end extraction of Amex Platinum card data."""
        card_data = extract_from_url(AMEX_PLATINUM_URL)

        print(f"\nExtracted card data:")
        print(f"  Name: {card_data.name}")
        print(f"  Issuer: {card_data.issuer}")
        print(f"  Annual Fee: ${card_data.annual_fee}")
        print(f"  Credits: {len(card_data.credits)}")

        # Verify extraction
        assert EXPECTED_CARD_NAME_CONTAINS.lower() in card_data.name.lower(), \
            f"Card name should contain '{EXPECTED_CARD_NAME_CONTAINS}', got '{card_data.name}'"

        assert EXPECTED_ISSUER.lower() in card_data.issuer.lower(), \
            f"Issuer should be '{EXPECTED_ISSUER}', got '{card_data.issuer}'"

        # Amex Platinum should have annual fee > 0
        assert card_data.annual_fee > 0, "Annual fee should be positive"

        # Amex Platinum should have credits/benefits
        assert len(card_data.credits) > 0, "Should extract at least one credit/benefit"

        print(f"\nOK - Successfully extracted Amex Platinum card data!")
        if card_data.signup_bonus:
            print(f"  SUB: {card_data.signup_bonus.points_or_cash}")
        for credit in card_data.credits[:5]:
            print(f"  - {credit.name}: ${credit.amount} ({credit.frequency})")
        if len(card_data.credits) > 5:
            print(f"  ... and {len(card_data.credits) - 5} more credits")


if __name__ == "__main__":
    # Allow running directly for quick testing
    import sys

    print("=" * 60)
    print("Amex Platinum Extraction Test")
    print("=" * 60)

    # Test fetch
    print("\n[1/2] Testing fetch...")
    try:
        content = fetch_card_page(AMEX_PLATINUM_URL)
        print(f"OK - Fetched {len(content):,} characters")
    except FetchError as e:
        print(f"FAIL - Fetch failed: {e}")
        sys.exit(1)

    # Test extraction
    print("\n[2/2] Testing extraction pipeline...")
    try:
        card_data = extract_from_url(AMEX_PLATINUM_URL)
        print(f"OK - Extracted: {card_data.name}")
        print(f"  Issuer: {card_data.issuer}")
        print(f"  Annual Fee: ${card_data.annual_fee}")
        if card_data.signup_bonus:
            print(f"  SUB: {card_data.signup_bonus.points_or_cash}")
        print(f"  Credits ({len(card_data.credits)}):")
        for c in card_data.credits[:5]:
            print(f"    - {c.name}: ${c.amount}/{c.frequency}")
        if len(card_data.credits) > 5:
            print(f"    ... and {len(card_data.credits) - 5} more")
    except ExtractionError as e:
        print(f"FAIL - Extraction failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
