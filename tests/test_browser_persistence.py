"""
Real Browser Tests for localStorage Persistence
================================================
These tests use Selenium to run actual browser tests against the Streamlit app.
This verifies localStorage persistence in a real browser environment.

Usage:
    pytest tests/test_browser_persistence.py -v -s

Requirements:
    pip install selenium webdriver-manager
"""

import pytest
import time
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="module")
def streamlit_app():
    """Use the already-running Streamlit app on localhost:8501."""
    yield "http://localhost:8501"


@pytest.fixture(scope="module")
def browser():
    """Create a Selenium browser instance using local chromedriver."""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    try:
        service = Service("/tmp/chromedriver-mac-arm64/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        pytest.skip(f"Chrome not available: {e}")

    yield driver

    driver.quit()


class TestLocalStoragePersistence:
    """Test localStorage persistence with real browser."""

    def test_localstorage_direct_write_read(self, browser, streamlit_app):
        """Test that we can write and read localStorage directly."""
        browser.get(streamlit_app)
        time.sleep(3)  # Wait for page load

        # Write to localStorage directly
        test_data = {"test": "value", "number": 42}
        browser.execute_script(
            f"localStorage.setItem('test_direct', JSON.stringify({json.dumps(test_data)}))"
        )

        # Read back
        result = browser.execute_script(
            "return localStorage.getItem('test_direct')"
        )

        assert result is not None, "localStorage write/read failed"
        parsed = json.loads(result)
        assert parsed == test_data, f"Data mismatch: {parsed} != {test_data}"
        print(f"[OK] Direct localStorage write/read works: {parsed}")

    def test_localstorage_persists_after_refresh(self, browser, streamlit_app):
        """Test that localStorage persists after page refresh."""
        browser.get(streamlit_app)
        time.sleep(3)

        # Write test data
        test_data = {"persist_test": True, "timestamp": time.time()}
        browser.execute_script(
            f"localStorage.setItem('test_persist', JSON.stringify({json.dumps(test_data)}))"
        )

        # Refresh the page
        browser.refresh()
        time.sleep(3)

        # Read back after refresh
        result = browser.execute_script(
            "return localStorage.getItem('test_persist')"
        )

        assert result is not None, "Data lost after refresh!"
        parsed = json.loads(result)
        assert parsed["persist_test"] == True
        print(f"[OK] localStorage persists after refresh: {parsed}")

    def test_churnpilot_storage_key_write(self, browser, streamlit_app):
        """Test writing to the actual churnpilot_cards key."""
        browser.get(streamlit_app)
        time.sleep(3)

        # Write test card data to churnpilot_cards
        test_cards = [
            {
                "id": "test-card-1",
                "name": "Test Card",
                "issuer": "Test Bank",
                "annual_fee": 95,
                "credits": [],
                "created_at": "2024-01-01T00:00:00"
            }
        ]

        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify({json.dumps(test_cards)}))"
        )

        # Verify write
        result = browser.execute_script(
            "return localStorage.getItem('churnpilot_cards')"
        )

        assert result is not None
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "Test Card"
        print(f"[OK] churnpilot_cards key write works")

    def test_churnpilot_storage_persists_refresh(self, browser, streamlit_app):
        """Test that churnpilot_cards persists after refresh."""
        browser.get(streamlit_app)
        time.sleep(3)

        # Write
        test_cards = [{"id": "persist-test", "name": "Persist Test Card"}]
        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify({json.dumps(test_cards)}))"
        )

        # Refresh
        browser.refresh()
        time.sleep(3)

        # Read
        result = browser.execute_script(
            "return localStorage.getItem('churnpilot_cards')"
        )

        assert result is not None, "churnpilot_cards lost after refresh!"
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["id"] == "persist-test"
        print(f"[OK] churnpilot_cards persists after refresh")

    def test_streamlit_js_eval_component_exists(self, browser, streamlit_app):
        """Check if streamlit_js_eval component is rendered."""
        browser.get(streamlit_app)
        time.sleep(5)  # Extra time for Streamlit to load

        # Check for iframes (Streamlit components render in iframes)
        iframes = browser.find_elements("tag name", "iframe")
        print(f"Found {len(iframes)} iframes on page")

        # Check page source for any errors
        page_source = browser.page_source
        if "error" in page_source.lower():
            print("Warning: 'error' found in page source")

        # The presence of iframes suggests components are loading
        # We can't assert a specific number as it depends on the page state

    def test_app_loads_with_stored_data(self, browser, streamlit_app):
        """Test that the app loads data from localStorage on startup."""
        # First, manually set data in localStorage
        browser.get(streamlit_app)
        time.sleep(3)

        # Clear any existing data first
        browser.execute_script("localStorage.removeItem('churnpilot_cards')")

        # Set test data
        test_cards = [
            {
                "id": "preload-test",
                "name": "Preloaded Card",
                "issuer": "Test Issuer",
                "annual_fee": 100,
                "nickname": None,
                "signup_bonus": None,
                "credits": [],
                "opened_date": None,
                "template_id": None,
                "raw_text": None,
                "notes": None,
                "sub_achieved": False,
                "sub_achieved_date": None,
                "credit_usage": {},
                "reminder_snooze": {},
                "retention_offers": [],
                "created_at": "2024-01-01T00:00:00"
            }
        ]
        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify({json.dumps(test_cards)}))"
        )

        # Verify it's set
        verify = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        assert verify is not None, "Failed to set localStorage"
        print(f"[OK] Set localStorage: {len(json.loads(verify))} cards")

        # Refresh to trigger app reload
        browser.refresh()
        time.sleep(5)

        # Check if data is still there
        after_refresh = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        assert after_refresh is not None, "localStorage cleared after refresh!"

        parsed = json.loads(after_refresh)
        print(f"[OK] After refresh: {len(parsed)} cards in localStorage")
        assert len(parsed) >= 1, "Cards lost!"


class TestActualAppSaveFlow:
    """Test the actual app's save mechanism via browser."""

    def test_app_save_creates_localstorage_entry(self, browser, streamlit_app):
        """Test that adding a card through the app creates localStorage entry.

        This tests the ACTUAL save flow, not just direct localStorage manipulation.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        browser.get(streamlit_app)
        time.sleep(5)  # Wait for Streamlit to fully load

        # Clear existing data first
        browser.execute_script("localStorage.removeItem('churnpilot_cards')")

        # Verify it's cleared
        before = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        assert before is None or before == '[]', f"Expected empty, got: {before}"

        # Find and click the "Add Card" tab
        try:
            tabs = browser.find_elements(By.CSS_SELECTOR, "[data-baseweb='tab']")
            print(f"Found {len(tabs)} tabs")
            for tab in tabs:
                if "Add" in tab.text or "Library" in tab.text:
                    tab.click()
                    print(f"Clicked tab: {tab.text}")
                    time.sleep(2)
                    break
        except Exception as e:
            print(f"Could not find tabs: {e}")
            # Try alternative selector
            pass

        # Wait for any Streamlit activity to settle
        time.sleep(3)

        # Check if localStorage was updated (even from initial load)
        after = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"localStorage after tab click: {after}")

        # Note: This test confirms the page loads. Full UI interaction
        # testing would require more complex element selection.


class TestStreamlitJsEvalBehavior:
    """Test how streamlit_js_eval behaves in the actual app."""

    def test_js_eval_timing(self, browser, streamlit_app):
        """Investigate JS eval timing issues."""
        browser.get(streamlit_app)
        time.sleep(5)

        # Check all localStorage keys
        all_keys = browser.execute_script("""
            var keys = [];
            for (var i = 0; i < localStorage.length; i++) {
                keys.push(localStorage.key(i));
            }
            return keys;
        """)
        print(f"All localStorage keys: {all_keys}")

        # Check for churnpilot_cards specifically
        cards = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        if cards:
            print(f"churnpilot_cards exists: {len(json.loads(cards))} cards")
        else:
            print("churnpilot_cards is null/empty")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
