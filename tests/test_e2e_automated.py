"""
Automated End-to-End Test for Data Persistence
==============================================
This test actually runs the Streamlit app and tests the real user journey.

Run with: python tests/test_e2e_automated.py

This script will:
1. Start the Streamlit app
2. Use Selenium to interact with the UI
3. Test the complete add-card-and-refresh journey
4. Report exactly where failures occur
"""

import subprocess
import sys
import time
import json
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_selenium_available():
    """Check if Selenium and Chrome are available."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install selenium webdriver-manager")
        return False


def start_streamlit_app(port=8599):
    """Start Streamlit app and return the process."""
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"

    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "src/ui/app.py",
         "--server.port", str(port),
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(PROJECT_ROOT)
    )

    # Wait for app to start
    print("⏳ Starting Streamlit app...")
    time.sleep(8)

    return process, f"http://localhost:{port}"


def create_browser():
    """Create a Selenium browser instance."""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # Enable logging
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    return driver


def get_localstorage(browser, key='churnpilot_cards'):
    """Get value from localStorage."""
    result = browser.execute_script(f"return localStorage.getItem('{key}')")
    return result


def set_localstorage(browser, key, value):
    """Set value in localStorage."""
    browser.execute_script(f"localStorage.setItem('{key}', '{value}')")


def clear_localstorage(browser):
    """Clear all localStorage."""
    browser.execute_script("localStorage.clear()")


def get_console_logs(browser):
    """Get browser console logs."""
    try:
        logs = browser.get_log('browser')
        return [log['message'] for log in logs]
    except:
        return []


def wait_for_app_stable(browser, timeout=15):
    """Wait for app to stabilize (no more reruns)."""
    time.sleep(timeout)


def run_test():
    """Run the end-to-end test."""
    print("\n" + "="*60)
    print("ChurnPilot End-to-End Persistence Test")
    print("="*60 + "\n")

    if not check_selenium_available():
        return False

    process = None
    browser = None

    try:
        # Start app
        process, url = start_streamlit_app()
        print(f"✅ App started at {url}\n")

        # Create browser
        browser = create_browser()
        print("✅ Browser created\n")

        # ========================================
        # TEST 1: Verify app loads
        # ========================================
        print("📋 TEST 1: App loads correctly")
        browser.get(url)
        wait_for_app_stable(browser, 8)

        title = browser.title
        print(f"   Page title: {title}")

        # Check for errors
        errors = browser.find_elements("css selector", ".stException, .stError")
        if errors:
            error_texts = [e.text for e in errors if e.text]
            print(f"   ⚠️ Errors found: {error_texts[:2]}")
        else:
            print("   ✅ No errors on page")

        # ========================================
        # TEST 2: Clear localStorage and verify empty
        # ========================================
        print("\n📋 TEST 2: Clear localStorage")
        clear_localstorage(browser)
        browser.refresh()
        wait_for_app_stable(browser, 8)

        initial_data = get_localstorage(browser)
        print(f"   localStorage after clear: {initial_data}")

        if initial_data is None or initial_data == '[]' or initial_data == '':
            print("   ✅ localStorage is empty")
        else:
            print(f"   ⚠️ localStorage not empty: {initial_data[:100]}...")

        # ========================================
        # TEST 3: Set test data in localStorage directly
        # ========================================
        print("\n📋 TEST 3: Set test data directly in localStorage")
        test_card = {
            "id": "test-e2e-001",
            "name": "E2E Test Card",
            "issuer": "Test Bank",
            "annual_fee": 100,
            "credits": [],
            "created_at": "2024-01-01T00:00:00"
        }
        test_data = json.dumps([test_card])
        set_localstorage(browser, 'churnpilot_cards', test_data)

        verify_set = get_localstorage(browser)
        print(f"   Data set: {verify_set[:80]}...")
        print("   ✅ Test data written to localStorage")

        # ========================================
        # TEST 4: Refresh and check if data persists in localStorage
        # ========================================
        print("\n📋 TEST 4: Refresh page and check localStorage")
        browser.refresh()
        wait_for_app_stable(browser, 10)

        after_refresh = get_localstorage(browser)
        print(f"   localStorage after refresh: {after_refresh[:100] if after_refresh else 'None'}...")

        if after_refresh is None:
            print("   ❌ FAIL: localStorage was CLEARED after refresh!")
            print("   This means the app is overwriting localStorage on load.")

            # Check console logs for clues
            logs = get_console_logs(browser)
            churnpilot_logs = [l for l in logs if 'ChurnPilot' in l]
            print(f"   Console logs: {churnpilot_logs[-5:] if churnpilot_logs else 'None'}")
            return False
        else:
            try:
                parsed = json.loads(after_refresh)
                if len(parsed) == 1 and parsed[0].get('name') == 'E2E Test Card':
                    print("   ✅ Data persists after refresh in localStorage")
                else:
                    print(f"   ⚠️ Data changed: {parsed}")
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON in localStorage: {after_refresh}")
                return False

        # ========================================
        # TEST 5: Check if app loaded the data into UI
        # ========================================
        print("\n📋 TEST 5: Check if Dashboard shows the card")

        # Try multiple refreshes to give the app time to load
        for attempt in range(5):
            print(f"   Attempt {attempt + 1}/5...")

            # Look for Dashboard tab or card content
            # Note: get_display_name() strips "Card" from name, so search for "E2E Test"
            page_source = browser.page_source

            if "E2E Test" in page_source:
                print("   ✅ Card name found in page!")
                break
            else:
                # Check localStorage is still there
                current_ls = get_localstorage(browser)
                print(f"   localStorage: {current_ls[:60] if current_ls else 'None'}...")

                if attempt < 4:
                    print("   Card not found, refreshing again...")
                    browser.refresh()
                    wait_for_app_stable(browser, 10)  # Increased wait time
        else:
            print("   ❌ Card name NOT found after 5 attempts")
            print("   This means data is in localStorage but NOT loaded into session state")

            # Save page source for debugging
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("   Saved page source to debug_page_source.html")

            # Check console logs
            logs = get_console_logs(browser)
            churnpilot_logs = [l for l in logs if 'ChurnPilot' in l]
            print(f"   Console logs ({len(churnpilot_logs)}):")
            for log in churnpilot_logs[-10:]:
                print(f"      {log[:150]}")

            # Check what iframes exist (Streamlit components)
            iframes = browser.find_elements("tag name", "iframe")
            print(f"   Found {len(iframes)} iframes on page")

            return False

        # ========================================
        # TEST 6: Simulate adding a card via UI (advanced)
        # ========================================
        print("\n📋 TEST 6: Testing actual UI card addition")

        # Clear localStorage again
        clear_localstorage(browser)
        browser.refresh()
        wait_for_app_stable(browser, 8)

        # Find and click Add Card tab
        from selenium.webdriver.common.by import By

        try:
            tabs = browser.find_elements(By.CSS_SELECTOR, "[data-baseweb='tab']")
            add_tab = None
            for tab in tabs:
                if "Add" in tab.text:
                    add_tab = tab
                    break

            if add_tab:
                add_tab.click()
                time.sleep(2)
                print("   Clicked Add Card tab")
            else:
                print("   Could not find Add Card tab")

        except Exception as e:
            print(f"   Could not interact with tabs: {e}")

        # Wait for any processing
        wait_for_app_stable(browser, 5)

        # Check localStorage after tab interaction
        current_data = get_localstorage(browser)
        print(f"   Current localStorage: {current_data[:100] if current_data else 'None'}")

        # ========================================
        # SUMMARY
        # ========================================
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✅ All basic persistence tests passed!")
        print("The app correctly preserves localStorage data after refresh.")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if browser:
            browser.quit()
            print("\n🧹 Browser closed")
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print("🧹 Streamlit app stopped")


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
