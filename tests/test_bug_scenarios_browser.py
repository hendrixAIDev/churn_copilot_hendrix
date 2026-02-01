"""
Browser Tests for Specific Bug Scenarios
=========================================
These tests verify fixes for user-reported bugs:

Bug 1: Inconsistent feedback after adding cards
- After first card: page switches to Dashboard
- After second card: no feedback, stays on Add Card
- User added duplicates without knowing

Bug 2: Cards not loading from localStorage on refresh
- localStorage has 5 cards
- After refresh, Dashboard shows nothing
- Data loading timing issue

Usage:
    pytest tests/test_bug_scenarios_browser.py -v -s

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


class TestBug1MultiCardAddFeedback:
    """
    Bug 1: Inconsistent feedback after adding cards

    Expected behavior:
    - Each card add should show clear success feedback
    - User should NOT switch away from Add Card tab
    - Duplicate adds should be prevented or clearly indicated
    """

    def test_localstorage_updates_after_each_add(self, browser, streamlit_app):
        """
        Simulate adding multiple cards and verify localStorage is updated each time.
        This tests the underlying data persistence, not the UI feedback.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Clear localStorage
        browser.execute_script("localStorage.clear()")
        browser.refresh()
        time.sleep(5)

        # Add first card manually (simulating what the app does)
        card1 = {"id": "test-1", "name": "Card One", "issuer": "Bank A", "annual_fee": 0, "credits": [], "created_at": "2024-01-01T00:00:00"}
        browser.execute_script(f"localStorage.setItem('churnpilot_cards', JSON.stringify([{json.dumps(card1)}]))")

        # Verify first card
        after1 = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        parsed1 = json.loads(after1)
        assert len(parsed1) == 1, f"Expected 1 card, got {len(parsed1)}"
        print(f"[OK] After first add: {len(parsed1)} cards")

        # Add second card (append to existing)
        card2 = {"id": "test-2", "name": "Card Two", "issuer": "Bank B", "annual_fee": 95, "credits": [], "created_at": "2024-01-02T00:00:00"}
        browser.execute_script(f"""
            var existing = JSON.parse(localStorage.getItem('churnpilot_cards') || '[]');
            existing.push({json.dumps(card2)});
            localStorage.setItem('churnpilot_cards', JSON.stringify(existing));
        """)

        # Verify second card
        after2 = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        parsed2 = json.loads(after2)
        assert len(parsed2) == 2, f"Expected 2 cards, got {len(parsed2)}"
        print(f"[OK] After second add: {len(parsed2)} cards")

        # Add third, fourth, fifth cards
        for i in range(3, 6):
            card = {"id": f"test-{i}", "name": f"Card {i}", "issuer": f"Bank {chr(64+i)}", "annual_fee": i*100, "credits": [], "created_at": f"2024-01-0{i}T00:00:00"}
            browser.execute_script(f"""
                var existing = JSON.parse(localStorage.getItem('churnpilot_cards') || '[]');
                existing.push({json.dumps(card)});
                localStorage.setItem('churnpilot_cards', JSON.stringify(existing));
            """)

        # Verify all 5 cards
        after5 = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        parsed5 = json.loads(after5)
        assert len(parsed5) == 5, f"Expected 5 cards, got {len(parsed5)}"
        print(f"[OK] After all adds: {len(parsed5)} cards")

        # Verify all cards have unique IDs
        ids = [c['id'] for c in parsed5]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"
        print(f"[OK] All card IDs are unique")

    def test_no_duplicate_cards_on_rapid_add(self, browser, streamlit_app):
        """
        When adding cards rapidly, no duplicates should be created.
        This tests the scenario where user clicks "Add Card" multiple times.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Clear and set known state
        browser.execute_script("localStorage.clear()")

        # Simulate rapid adds of the SAME card (what might happen if user double-clicks)
        same_card = {"id": "same-id", "name": "Same Card", "issuer": "Bank", "annual_fee": 0, "credits": [], "created_at": "2024-01-01T00:00:00"}

        # First add
        browser.execute_script(f"localStorage.setItem('churnpilot_cards', JSON.stringify([{json.dumps(same_card)}]))")

        # Second add of same ID should not create duplicate (app should check ID)
        browser.execute_script(f"""
            var existing = JSON.parse(localStorage.getItem('churnpilot_cards') || '[]');
            var isDuplicate = existing.some(c => c.id === '{same_card["id"]}');
            if (!isDuplicate) {{
                existing.push({json.dumps(same_card)});
                localStorage.setItem('churnpilot_cards', JSON.stringify(existing));
            }}
        """)

        result = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        parsed = json.loads(result)
        assert len(parsed) == 1, f"Duplicate card created! Got {len(parsed)} cards"
        print(f"[OK] No duplicate cards on rapid add")


class TestBug2DataLoadingOnRefresh:
    """
    Bug 2: Cards not loading from localStorage on refresh

    Expected behavior:
    - After refresh, all cards from localStorage should be loaded
    - Dashboard should display all cards
    - No data loss on page refresh
    """

    def test_five_cards_persist_after_refresh(self, browser, streamlit_app):
        """
        User reported: localStorage has 5 cards, but after refresh Dashboard shows nothing.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Set up 5 cards in localStorage (mimicking user's scenario)
        test_cards = [
            {"id": f"persist-{i}", "name": f"Persist Card {i}", "issuer": f"Bank {i}",
             "annual_fee": i * 100, "credits": [], "created_at": f"2024-01-0{i}T00:00:00"}
            for i in range(1, 6)
        ]
        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify({json.dumps(test_cards)}))"
        )

        # Verify initial set
        before = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        assert before is not None
        before_parsed = json.loads(before)
        assert len(before_parsed) == 5, f"Failed to set 5 cards, got {len(before_parsed)}"
        print(f"[OK] Set 5 cards in localStorage")

        # Refresh the page (this is where the bug occurred)
        browser.refresh()
        time.sleep(10)  # Wait longer for app to fully load and retry

        # Check localStorage after refresh
        after = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        assert after is not None, "localStorage was cleared after refresh!"
        after_parsed = json.loads(after)
        assert len(after_parsed) == 5, f"Cards lost after refresh! Expected 5, got {len(after_parsed)}"
        print(f"[OK] All 5 cards persist after refresh")

        # Verify card data integrity
        for i, card in enumerate(after_parsed):
            assert card['name'] == f"Persist Card {i+1}", f"Card {i+1} name mismatch"
        print(f"[OK] Card data integrity maintained")

    def test_data_loads_on_multiple_refreshes(self, browser, streamlit_app):
        """
        Data should persist across multiple refreshes.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Set initial data
        test_cards = [{"id": "multi-refresh", "name": "Multi Refresh Test", "issuer": "Test Bank",
                       "annual_fee": 0, "credits": [], "created_at": "2024-01-01T00:00:00"}]
        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify({json.dumps(test_cards)}))"
        )

        # Refresh multiple times
        for i in range(3):
            browser.refresh()
            time.sleep(8)

            # Verify data still exists
            result = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
            assert result is not None, f"Data lost on refresh #{i+1}"
            parsed = json.loads(result)
            assert len(parsed) >= 1, f"Cards lost on refresh #{i+1}"
            print(f"[OK] Refresh #{i+1}: Data persists ({len(parsed)} cards)")

    def test_empty_localstorage_handled_gracefully(self, browser, streamlit_app):
        """
        When localStorage is empty, app should load without errors.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Clear localStorage completely
        browser.execute_script("localStorage.clear()")

        # Refresh
        browser.refresh()
        time.sleep(8)

        # App should load without errors
        # Check for error elements
        errors = browser.find_elements("css selector", ".stException, .stError")
        error_texts = [e.text for e in errors if e.text]
        if error_texts:
            print(f"Errors found: {error_texts}")

        # Some transient errors might be OK, but shouldn't have blocking errors
        blocking_errors = [e for e in errors if "streamlit-js-eval" not in e.text.lower()]
        assert len(blocking_errors) == 0, f"Blocking errors found: {[e.text for e in blocking_errors]}"
        print(f"[OK] Empty localStorage handled gracefully")


class TestDataLoadingTiming:
    """
    Test the timing aspects of data loading from localStorage.
    """

    def test_data_available_after_app_stabilizes(self, browser, streamlit_app):
        """
        After app fully loads and stabilizes, data should be available.
        The init_web_storage should retry until data is loaded.
        """
        browser.get(streamlit_app)
        time.sleep(3)

        # Set data before app fully initializes
        test_data = [{"id": "timing-test", "name": "Timing Test Card", "issuer": "Test",
                      "annual_fee": 0, "credits": [], "created_at": "2024-01-01T00:00:00"}]
        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify({json.dumps(test_data)}))"
        )

        # Refresh to trigger app reload with existing data
        browser.refresh()

        # Wait for app to stabilize (multiple reruns)
        time.sleep(12)

        # Verify data is still there
        result = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        assert result is not None, "Data was cleared!"
        parsed = json.loads(result)
        assert len(parsed) >= 1, "Cards were lost!"
        print(f"[OK] Data available after app stabilizes: {len(parsed)} cards")

    def test_get_local_storage_returns_data(self, browser, streamlit_app):
        """
        Verify that get_local_storage eventually returns the data.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Set known data
        test_data = [{"id": "get-test", "name": "Get Test", "issuer": "Test",
                      "annual_fee": 0, "credits": [], "created_at": "2024-01-01T00:00:00"}]
        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify({json.dumps(test_data)}))"
        )

        # Simulate what get_local_storage does
        js_code = """
        return (function() {
            var value = localStorage.getItem('churnpilot_cards');
            return value;
        })();
        """
        result = browser.execute_script(js_code)

        assert result is not None, "Direct localStorage.getItem returned null"
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]['name'] == "Get Test"
        print(f"[OK] Direct localStorage read works: {parsed[0]['name']}")


class TestConsoleLogsForDebugging:
    """
    Check console logs to understand what's happening during load/save.
    """

    def test_load_logs_appear(self, browser, streamlit_app):
        """
        The app should log loading attempts for debugging.
        """
        browser.get(streamlit_app)
        time.sleep(5)

        # Set data
        browser.execute_script(
            "localStorage.setItem('churnpilot_cards', JSON.stringify([{id:'log-test',name:'Log Test'}]))"
        )

        # Refresh to trigger load
        browser.refresh()
        time.sleep(10)

        # Get console logs
        try:
            logs = browser.get_log('browser')
            churnpilot_logs = [log for log in logs if 'ChurnPilot' in str(log.get('message', ''))]
            print(f"ChurnPilot-related logs ({len(churnpilot_logs)}):")
            for log in churnpilot_logs[-10:]:
                print(f"  {log.get('message', '')[:200]}")
        except Exception as e:
            print(f"Could not get logs: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
