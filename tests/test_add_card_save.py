"""
Test adding a card through the UI and checking if it saves to localStorage.
"""

import subprocess
import sys
import time
import json
import os
import threading
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_test():
    print("\n" + "="*60)
    print("Add Card Save Test")
    print("="*60 + "\n")

    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["PYTHONUNBUFFERED"] = "1"

    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "src/ui/app.py",
         "--server.port", "8599",
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=str(PROJECT_ROOT),
        text=True,
        bufsize=1
    )

    logs = []
    def read_logs():
        for line in process.stdout:
            logs.append(line.strip())
            if "[ChurnPilot]" in line:
                print(f"  SERVER: {line.strip()}")

    log_thread = threading.Thread(target=read_logs, daemon=True)
    log_thread.start()

    print("Starting Streamlit app...")
    time.sleep(5)

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        service = Service(ChromeDriverManager().install())
        browser = webdriver.Chrome(service=service, options=options)

        url = "http://localhost:8599"

        # Step 1: Load and clear
        print("\n[Step 1] Load page and clear localStorage...")
        browser.get(url)
        time.sleep(10)
        browser.execute_script("localStorage.clear()")
        browser.refresh()
        time.sleep(10)

        # Step 2: Navigate to Add Card tab
        print("\n[Step 2] Navigate to Add Card tab...")
        tabs = browser.find_elements(By.CSS_SELECTOR, "[data-baseweb='tab']")
        for tab in tabs:
            print(f"   Found tab: {tab.text}")
            if "Add" in tab.text:
                tab.click()
                time.sleep(2)
                print(f"   Clicked: {tab.text}")
                break

        # Step 3: Select a card from the library
        print("\n[Step 3] Selecting a card from the library...")
        time.sleep(2)

        # There are TWO selectboxes:
        # 1. Issuer filter (All Issuers, American Express, etc.)
        # 2. Card selector (-- Select card --, specific cards)
        selectboxes = browser.find_elements(By.CSS_SELECTOR, "[data-testid='stSelectbox']")
        print(f"   Found {len(selectboxes)} selectboxes")

        if len(selectboxes) >= 2:
            # First, optionally select an issuer (the first selectbox)
            # Skip this for now, keep "All Issuers"

            # Click the SECOND selectbox (card selector)
            print("   Clicking card selector (second selectbox)...")
            selectboxes[1].click()
            time.sleep(1)

            # Look for card options
            options_list = browser.find_elements(By.CSS_SELECTOR, "[role='option']")
            print(f"   Found {len(options_list)} card options")

            # Print available options
            for i, opt in enumerate(options_list[:5]):
                print(f"   Option {i}: {opt.text[:50]}...")

            # Select the second option (first real card, skip placeholder)
            if len(options_list) > 1:
                options_list[1].click()
                time.sleep(2)
                print("   Selected a card template")

        # Step 4: Check localStorage after selection
        print("\n[Step 4] Check localStorage after selection...")
        time.sleep(3)
        ls_after_select = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   localStorage: {ls_after_select[:80] if ls_after_select else 'None'}...")

        # Step 5: Look for Add button and click it
        print("\n[Step 5] Looking for Add button...")
        buttons = browser.find_elements(By.CSS_SELECTOR, "button")
        add_button = None
        for btn in buttons:
            btn_text = btn.text.strip()
            if btn_text and ("Add" in btn_text or "Save" in btn_text):
                print(f"   Found button: '{btn_text}'")
                if "Add Card" in btn_text or btn_text == "Add":
                    add_button = btn

        if add_button:
            print(f"   Clicking add button...")
            add_button.click()
            time.sleep(8)  # Wait for save, rerun, and JS execution

        # Step 6: Check localStorage after adding (with retries)
        print("\n[Step 6] Check localStorage after adding (with retries)...")
        for attempt in range(5):
            time.sleep(2)
            ls_check = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
            if ls_check:
                print(f"   Attempt {attempt+1}: Found data!")
                break
            else:
                print(f"   Attempt {attempt+1}: Still empty, waiting...")
        ls_after_add = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   localStorage: {ls_after_add[:100] if ls_after_add else 'None'}...")

        if ls_after_add:
            cards = json.loads(ls_after_add)
            print(f"   Card count: {len(cards)}")
            for card in cards:
                print(f"   - {card.get('name', 'unnamed')}")

        # Step 7: IMMEDIATE refresh
        print("\n[Step 7] Immediate refresh...")
        browser.refresh()
        time.sleep(8)

        ls_after_refresh = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   localStorage after refresh: {ls_after_refresh[:100] if ls_after_refresh else 'None'}...")

        if ls_after_refresh:
            cards = json.loads(ls_after_refresh)
            print(f"   Card count after refresh: {len(cards)}")
        else:
            print("   FAIL: localStorage is empty after refresh!")

        # Check browser console logs
        print("\n[Browser Console Logs]")
        try:
            browser_logs = browser.get_log('browser')
            for log in browser_logs:
                if 'ChurnPilot' in str(log.get('message', '')):
                    print(f"   {log['message'][:100]}")
        except:
            pass

        browser.quit()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except:
            process.kill()

        # Print server logs
        print("\n[Server Logs - Save related]")
        for log in logs:
            if "Save" in log or "Sync" in log or "localStorage" in log.lower():
                print(f"   {log}")

        print("\nApp stopped.")


if __name__ == "__main__":
    run_test()
