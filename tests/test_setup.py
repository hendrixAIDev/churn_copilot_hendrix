"""Setup verification tests.

Run this first to verify all dependencies are correctly installed:
    python tests/test_setup.py

Or with pytest:
    pytest tests/test_setup.py -v
"""

import sys


def test_core_imports():
    """Test that all core modules can be imported."""
    print("\n[1/4] Testing core imports...")
    try:
        from src.core import (
            CardStorage,
            extract_from_url,
            extract_from_text,
            fetch_card_page,
        )
        print("OK - Core modules imported successfully")
        return True
    except ImportError as e:
        print(f"FAIL - Import failed: {e}")
        return False


def test_anthropic_api():
    """Test that Anthropic API is configured."""
    print("\n[2/4] Testing Anthropic API...")
    import os
    from dotenv import load_dotenv
    from pathlib import Path

    # Load .env
    load_dotenv(Path(__file__).parent.parent / ".env")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("✗ ANTHROPIC_API_KEY not set in .env file")
        return False

    if not api_key.startswith("sk-ant-"):
        print("✗ ANTHROPIC_API_KEY doesn't look like a valid key")
        return False

    print(f"✓ API key configured (sk-ant-...{api_key[-4:]})")
    return True


def test_fetch_simple_page():
    """Test fetching a simple page via Jina Reader."""
    print("\n[3/4] Testing simple page fetch (via Jina Reader)...")
    try:
        from src.core.fetcher import fetch_card_page

        content = fetch_card_page("https://www.nerdwallet.com/", timeout=30)
        if len(content) > 100:
            print(f"✓ Fetched {len(content):,} characters from NerdWallet")
            return True
        else:
            print(f"✗ Content too short: {len(content)} chars")
            return False
    except Exception as e:
        print(f"✗ Fetch failed: {e}")
        return False


def test_fetch_amex_platinum():
    """Test fetching Amex Platinum card page via Jina Reader."""
    print("\n[4/5] Testing Amex Platinum fetch (public card page via Jina Reader)...")
    try:
        from src.core.fetcher import fetch_card_page

        # Use public card page, not login-required benefits page
        url = "https://www.americanexpress.com/us/credit-cards/card/platinum/"
        content = fetch_card_page(url, timeout=60)

        if len(content) < 500:
            print(f"✗ Content too short: {len(content)} chars (expected 500+)")
            return False

        # Check for expected keywords
        content_lower = content.lower()
        keywords = ["credit", "benefit", "platinum"]
        found = [kw for kw in keywords if kw in content_lower]

        if len(found) < 2:
            print(f"✗ Missing expected keywords. Found: {found}")
            return False

        print(f"✓ Fetched {len(content):,} characters from Amex Platinum")
        print(f"  Keywords found: {found}")
        return True
    except Exception as e:
        print(f"✗ Fetch failed: {e}")
        return False


def test_fetch_uscreditcardguide():
    """Test fetching from US Credit Card Guide."""
    print("\n[5/6] Testing US Credit Card Guide fetch...")
    try:
        from src.core.fetcher import fetch_card_page

        url = "https://www.uscreditcardguide.com/amex-platinum/"
        content = fetch_card_page(url, timeout=60)

        if len(content) < 500:
            print(f"✗ Fetched content too short: {len(content)} chars")
            return False

        # Check for expected keywords
        content_lower = content.lower()
        keywords = ["annual fee", "platinum", "credit", "benefit", "point"]
        found = [kw for kw in keywords if kw in content_lower]

        if len(found) < 3:
            print(f"✗ Missing expected keywords. Found: {found}")
            return False

        print(f"✓ Fetched {len(content):,} characters")
        print(f"  Keywords found: {found}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_extract_from_url_pipeline():
    """Test end-to-end extraction pipeline: URL -> Jina -> Claude -> CardData."""
    print("\n[6/6] Testing full extraction pipeline (URL -> Jina -> Claude)...")
    try:
        from src.core.pipeline import extract_from_url

        url = "https://www.uscreditcardguide.com/amex-platinum/"
        card_data = extract_from_url(url)

        # Verify we got a valid CardData object
        if not card_data.name:
            print("✗ Card name is empty")
            return False

        if "platinum" not in card_data.name.lower():
            print(f"✗ Card name doesn't contain 'platinum': {card_data.name}")
            return False

        if card_data.annual_fee <= 0:
            print(f"✗ Annual fee not extracted: {card_data.annual_fee}")
            return False

        print(f"✓ Extracted card data:")
        print(f"  Name: {card_data.name}")
        print(f"  Issuer: {card_data.issuer}")
        print(f"  Annual Fee: ${card_data.annual_fee}")
        if card_data.signup_bonus:
            print(f"  SUB: {card_data.signup_bonus.points_or_cash}")
        print(f"  Credits: {len(card_data.credits)} found")
        return True
    except Exception as e:
        print(f"✗ Pipeline failed: {e}")
        return False


def run_all_tests():
    """Run all setup verification tests."""
    print("=" * 60)
    print("ChurnPilot Setup Verification")
    print("=" * 60)

    results = []
    results.append(("Core imports", test_core_imports()))
    results.append(("Anthropic API", test_anthropic_api()))
    results.append(("Simple fetch", test_fetch_simple_page()))
    results.append(("Amex Platinum fetch", test_fetch_amex_platinum()))
    results.append(("US Credit Card Guide", test_fetch_uscreditcardguide()))
    results.append(("Full extraction pipeline", test_extract_from_url_pipeline()))

    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\nAll checks passed! You can now run the app:")
        print("  streamlit run src/ui/app.py")
    else:
        print("\nSome checks failed. Please fix the issues above.")
        print("\nQuick fixes:")
        print("  pip install -r requirements.txt")
        print("  # Create .env file with ANTHROPIC_API_KEY=your-key")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
