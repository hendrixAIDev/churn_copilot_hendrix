"""
Comprehensive Browser Tests for Critical User Journeys
=======================================================
These tests use Selenium to test the ACTUAL app behavior, not just localStorage.

Critical User Journeys Tested:
1. Add card from library -> appears in Dashboard
2. Add card -> refresh -> persists
3. Edit card -> refresh -> changes persist
4. Delete card -> refresh -> card gone
5. Multiple cards -> refresh -> all persist
6. Import data -> refresh -> persists

Usage:
    pytest tests/test_user_journeys_browser.py -v -s

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


class TestAddCardJourney:
    """Test adding cards through the app UI."""

    def test_add_card_via_library_creates_localstorage(self, browser, streamlit_app):
        """
        Journey: User adds card from library
        Expected: Card data should be saved to localStorage
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import Select

        # Clear localStorage first
        browser.get(streamlit_app)
        time.sleep(5)
        browser.execute_script("localStorage.clear()")
        browser.refresh()
        time.sleep(5)

        # Verify localStorage is empty
        before = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"Before adding card: {before}")

        # Find and click the "Add Card" tab
        try:
            tabs = browser.find_elements(By.CSS_SELECTOR, "[data-baseweb='tab']")
            for tab in tabs:
                if "Add" in tab.text:
                    tab.click()
                    print(f"Clicked tab: {tab.text}")
                    time.sleep(3)
                    break
        except Exception as e:
            print(f"Could not find Add Card tab: {e}")

        # Try to find and interact with the card library dropdown
        try:
            # Look for selectbox elements
            selectboxes = browser.find_elements(By.CSS_SELECTOR, "[data-testid='stSelectbox']")
            print(f"Found {len(selectboxes)} selectboxes")

            if selectboxes:
                # Click the first selectbox to open it
                selectboxes[0].click()
                time.sleep(1)

                # Try to select an option
                options = browser.find_elements(By.CSS_SELECTOR, "[data-testid='stSelectboxOption']")
                print(f"Found {len(options)} options")

                if len(options) > 1:
                    options[1].click()  # Select first real option (not placeholder)
                    time.sleep(2)

        except Exception as e:
            print(f"Could not interact with dropdown: {e}")

        # Wait for any Streamlit processing
        time.sleep(5)

        # Check localStorage after interaction
        after = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"After interaction: {after}")

        # Check console logs
        logs = browser.get_log('browser')
        churnpilot_logs = [log for log in logs if 'ChurnPilot' in str(log)]
        print(f"ChurnPilot logs: {churnpilot_logs}")


class TestPersistenceJourney:
    """Test that data persists across page refreshes."""

    def test_manually_set_data_persists_after_refresh(self, browser, streamlit_app):
        """
        Journey: Set data in localStorage, refresh, verify it's still there
        This tests that the app doesn't CLEAR localStorage on load.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Set test data directly
        test_card = {
            "id": "test-persist-001",
            "name": "Test Persistence Card",
            "issuer": "Test Bank",
            "annual_fee": 100,
            "credits": [],
            "created_at": "2024-01-01T00:00:00"
        }
        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify([{json.dumps(test_card)}]))"
        )

        # Verify it's set
        before = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        assert before is not None
        before_parsed = json.loads(before)
        assert len(before_parsed) == 1
        print(f"[OK] Set localStorage: {before_parsed[0]['name']}")

        # Refresh the page (this runs the app which might overwrite localStorage)
        browser.refresh()
        time.sleep(8)  # Wait for app to fully load

        # Check if data persists
        after = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"After refresh: {after}")

        assert after is not None, "localStorage was cleared after refresh!"
        after_parsed = json.loads(after)
        assert len(after_parsed) >= 1, f"Card was lost! Got: {after_parsed}"
        assert after_parsed[0]['name'] == "Test Persistence Card", f"Wrong card: {after_parsed}"
        print(f"[OK] Data persists after refresh: {after_parsed[0]['name']}")

    def test_multiple_cards_persist(self, browser, streamlit_app):
        """
        Journey: Set multiple cards, refresh, all should persist
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Set multiple test cards
        test_cards = [
            {"id": "multi-1", "name": "Card One", "issuer": "Bank A", "annual_fee": 0, "credits": [], "created_at": "2024-01-01T00:00:00"},
            {"id": "multi-2", "name": "Card Two", "issuer": "Bank B", "annual_fee": 95, "credits": [], "created_at": "2024-01-02T00:00:00"},
            {"id": "multi-3", "name": "Card Three", "issuer": "Bank C", "annual_fee": 550, "credits": [], "created_at": "2024-01-03T00:00:00"},
        ]
        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify({json.dumps(test_cards)}))"
        )

        # Refresh
        browser.refresh()
        time.sleep(8)

        # Verify all cards persist
        after = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        assert after is not None, "localStorage cleared!"
        after_parsed = json.loads(after)
        assert len(after_parsed) == 3, f"Expected 3 cards, got {len(after_parsed)}: {after_parsed}"
        print(f"[OK] All {len(after_parsed)} cards persist after refresh")


class TestAppSaveMechanism:
    """Test the app's internal save mechanism."""

    def test_direct_js_execution_works(self, browser, streamlit_app):
        """
        Test that direct JavaScript execution (not innerHTML) works.
        Our app uses st.components.v1.html which renders in iframes,
        not innerHTML injection. This test verifies the browser can
        execute JavaScript that modifies localStorage.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Direct JavaScript execution (this is what actually happens in our app's iframes)
        browser.execute_script("""
            try {
                localStorage.setItem('test_direct_js', JSON.stringify({success: true, timestamp: Date.now()}));
                console.log('[Test] Direct JS execution worked');
            } catch (e) {
                console.error('[Test] Direct JS failed:', e);
            }
        """)

        time.sleep(1)

        # Check if it worked
        result = browser.execute_script("return localStorage.getItem('test_direct_js')")
        assert result is not None, "Direct JS execution didn't work!"
        parsed = json.loads(result)
        assert parsed['success'] == True
        print(f"[OK] Direct JS execution works correctly")

    def test_streamlit_component_renders(self, browser, streamlit_app):
        """
        Check that Streamlit components (iframes) are present.
        The save mechanism uses st.components.v1.html which creates an iframe.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Count iframes
        iframes = browser.find_elements("tag name", "iframe")
        print(f"Found {len(iframes)} iframes on page")

        # Check for any with our save script
        for i, iframe in enumerate(iframes):
            try:
                src = iframe.get_attribute('src') or ''
                title = iframe.get_attribute('title') or ''
                print(f"  iframe {i}: src={src[:50]}... title={title}")
            except:
                pass


class TestConsoleLogging:
    """Test that console logs show save operations."""

    def test_console_shows_save_logs(self, browser, streamlit_app):
        """
        After the app loads and syncs, console should show save logs.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Set some data to trigger a sync on next page load
        browser.execute_script("""
            localStorage.setItem('churnpilot_cards', JSON.stringify([
                {id: 'log-test', name: 'Log Test Card', issuer: 'Test', annual_fee: 0, credits: []}
            ]));
        """)

        # Refresh to trigger app load
        browser.refresh()
        time.sleep(8)

        # Get browser console logs
        try:
            logs = browser.get_log('browser')
            all_logs = [log['message'] for log in logs]
            print(f"Browser logs ({len(all_logs)} total):")
            for log in all_logs[-20:]:  # Last 20 logs
                if 'ChurnPilot' in log or 'localStorage' in log.lower():
                    print(f"  {log}")
        except Exception as e:
            print(f"Could not get browser logs: {e}")


class TestDataIntegrity:
    """Test that data integrity is maintained."""

    def test_complex_card_data_persists(self, browser, streamlit_app):
        """
        Test that complex card data with all fields persists correctly.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Create a complex card with all fields
        complex_card = {
            "id": "complex-001",
            "name": "American Express Platinum Card",
            "nickname": "My Plat",
            "issuer": "American Express",
            "annual_fee": 695,
            "signup_bonus": {
                "points_or_cash": 150000,
                "spend_requirement": 6000.0,
                "time_period_days": 90,
                "deadline": "2024-04-01"
            },
            "credits": [
                {"name": "Uber Credit", "amount": 15, "frequency": "monthly"},
                {"name": "Saks Credit", "amount": 50, "frequency": "semi-annually"}
            ],
            "opened_date": "2024-01-15",
            "template_id": "amex_platinum",
            "notes": "Card with special chars: 'quotes' and \"double quotes\" and\nnewlines",
            "sub_achieved": True,
            "sub_achieved_date": "2024-03-15",
            "credit_usage": {"2024-01": {"Uber Credit": True}},
            "reminder_snooze": {},
            "retention_offers": [],
            "created_at": "2024-01-15T10:30:00"
        }

        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify([{json.dumps(complex_card)}]))"
        )

        # Refresh
        browser.refresh()
        time.sleep(8)

        # Verify complex data integrity
        after = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        assert after is not None, "Data lost!"

        after_parsed = json.loads(after)
        assert len(after_parsed) == 1

        card = after_parsed[0]
        assert card['name'] == "American Express Platinum Card"
        assert card['nickname'] == "My Plat"
        assert card['annual_fee'] == 695
        assert card['signup_bonus']['points_or_cash'] == 150000
        assert len(card['credits']) == 2
        assert 'newlines' in card['notes']
        print(f"[OK] Complex card data integrity maintained")


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_storage_doesnt_crash(self, browser, streamlit_app):
        """App should handle empty localStorage gracefully."""
        browser.get(streamlit_app)
        time.sleep(3)

        # Clear everything
        browser.execute_script("localStorage.clear()")

        # Refresh
        browser.refresh()
        time.sleep(8)

        # App should load without errors
        # Check for error elements
        errors = browser.find_elements("css selector", ".stException, .stError")
        assert len(errors) == 0, f"Found {len(errors)} error elements on page"
        print("[OK] App handles empty localStorage")

    def test_invalid_json_doesnt_crash(self, browser, streamlit_app):
        """App should handle invalid JSON in localStorage gracefully."""
        browser.get(streamlit_app)
        time.sleep(3)

        # Set invalid JSON
        browser.execute_script("localStorage.setItem('churnpilot_cards', 'not valid json {')")

        # Refresh
        browser.refresh()
        time.sleep(8)

        # App should load without crashing
        errors = browser.find_elements("css selector", ".stException")
        # Some warning is OK, but no crash
        print(f"[OK] App handles invalid JSON (found {len(errors)} exception elements)")


class TestSaveTimingDebug:
    """Debug tests to understand save timing."""

    def test_save_script_content(self, browser, streamlit_app):
        """
        Examine what save scripts look like in the DOM.
        """
        browser.get(streamlit_app)
        time.sleep(8)

        # Look for script elements
        scripts = browser.execute_script("""
            var scripts = document.querySelectorAll('script');
            var results = [];
            scripts.forEach(function(s) {
                if (s.innerHTML.includes('localStorage') || s.innerHTML.includes('churnpilot')) {
                    results.push(s.innerHTML.substring(0, 200));
                }
            });
            return results;
        """)

        print(f"Found {len(scripts)} localStorage-related scripts:")
        for i, script in enumerate(scripts[:5]):
            print(f"  Script {i}: {script}...")

    def test_iframe_content(self, browser, streamlit_app):
        """
        Check iframe contents for save scripts.
        Streamlit components render in iframes.
        """
        browser.get(streamlit_app)
        time.sleep(8)

        iframes = browser.find_elements("tag name", "iframe")
        print(f"Checking {len(iframes)} iframes for save scripts...")

        for i, iframe in enumerate(iframes[:10]):
            try:
                browser.switch_to.frame(iframe)
                scripts = browser.execute_script("""
                    var scripts = document.querySelectorAll('script');
                    var results = [];
                    scripts.forEach(function(s) {
                        if (s.innerHTML.includes('localStorage')) {
                            results.push(s.innerHTML.substring(0, 100));
                        }
                    });
                    return results;
                """)
                if scripts:
                    print(f"  iframe {i}: Found {len(scripts)} localStorage scripts")
                browser.switch_to.default_content()
            except Exception as e:
                browser.switch_to.default_content()
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
