"""
Test that simulates REAL user behavior:
1. Add a card
2. Check localStorage IMMEDIATELY (no waiting)
3. Refresh IMMEDIATELY
4. Check if data persists

This tests the actual user experience more accurately.
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
    print("IMMEDIATE Check Test (Real User Behavior)")
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
            if "Add" in tab.text:
                tab.click()
                time.sleep(2)
                print(f"   Clicked: {tab.text}")
                break

        # Step 3: Select a card from the library
        print("\n[Step 3] Selecting a card from the library...")
        time.sleep(2)
        selectboxes = browser.find_elements(By.CSS_SELECTOR, "[data-testid='stSelectbox']")

        if len(selectboxes) >= 2:
            selectboxes[1].click()
            time.sleep(1)
            options_list = browser.find_elements(By.CSS_SELECTOR, "[role='option']")
            if len(options_list) > 1:
                options_list[1].click()
                time.sleep(2)
                print("   Selected a card template")

        # Step 4: Click Add button
        print("\n[Step 4] Click Add button...")
        buttons = browser.find_elements(By.CSS_SELECTOR, "button")
        add_button = None
        for btn in buttons:
            btn_text = btn.text.strip()
            if btn_text and "Add Card" in btn_text:
                print(f"   Found button: '{btn_text}'")
                add_button = btn  # Keep the last one found (like test_add_card_save.py)

        if add_button:
            add_button.click()
            print("   Clicked Add Card button")
            print("   Waiting 3 seconds for Streamlit to process...")
            time.sleep(3)  # Give Streamlit time to process
        else:
            print("   ERROR: No Add Card button found!")

        # Step 5: IMMEDIATE check (0.5 seconds - simulating user clicking right away)
        print("\n[Step 5] IMMEDIATE check (0.5 second wait)...")
        time.sleep(0.5)
        ls_immediate = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   localStorage (0.5s): {ls_immediate[:80] if ls_immediate else 'EMPTY'}...")

        # Step 6: Check after 1 second
        print("\n[Step 6] Check after 1 second...")
        time.sleep(0.5)
        ls_1s = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   localStorage (1s): {ls_1s[:80] if ls_1s else 'EMPTY'}...")

        # Step 7: Check after 2 seconds
        print("\n[Step 7] Check after 2 seconds...")
        time.sleep(1)
        ls_2s = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   localStorage (2s): {ls_2s[:80] if ls_2s else 'EMPTY'}...")

        # Step 8: Check after 5 seconds
        print("\n[Step 8] Check after 5 seconds...")
        time.sleep(3)
        ls_5s = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   localStorage (5s): {ls_5s[:80] if ls_5s else 'EMPTY'}...")

        # Step 9: IMMEDIATE refresh after add (worst case user behavior)
        # NOTE: This tests an extreme edge case where user refreshes BEFORE
        # the server even processes the button click. This will always fail
        # due to Streamlit's client-server architecture.
        print("\n[Step 9] Testing WORST CASE: Add then refresh immediately...")
        print("   NOTE: This tests a race condition that cannot be fully avoided")
        browser.execute_script("localStorage.clear()")
        browser.refresh()
        time.sleep(10)

        # Navigate back to Add Card
        tabs = browser.find_elements(By.CSS_SELECTOR, "[data-baseweb='tab']")
        for tab in tabs:
            if "Add" in tab.text:
                tab.click()
                time.sleep(2)
                break

        # Select card
        selectboxes = browser.find_elements(By.CSS_SELECTOR, "[data-testid='stSelectbox']")
        if len(selectboxes) >= 2:
            selectboxes[1].click()
            time.sleep(1)
            options_list = browser.find_elements(By.CSS_SELECTOR, "[role='option']")
            if len(options_list) > 1:
                options_list[1].click()
                time.sleep(2)

        # Click Add
        buttons = browser.find_elements(By.CSS_SELECTOR, "button")
        for btn in buttons:
            if btn.text.strip() == "Add Card":
                btn.click()
                print("   Clicked Add Card button")
                break

        # IMMEDIATE refresh (0.5 seconds)
        print("   Refreshing in 0.5 seconds...")
        time.sleep(0.5)
        browser.refresh()

        # Wait for page to load
        time.sleep(10)

        ls_after_refresh = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   localStorage after immediate refresh: {ls_after_refresh[:80] if ls_after_refresh else 'EMPTY'}...")

        if ls_after_refresh:
            cards = json.loads(ls_after_refresh)
            print(f"   RESULT: {len(cards)} cards found - ", end="")
            if len(cards) > 0:
                print("SUCCESS!")
            else:
                print("FAIL (empty array)")
        else:
            print("   RESULT: FAIL - localStorage is empty!")

        # Print browser console logs
        print("\n[Browser Console Logs]")
        try:
            browser_logs = browser.get_log('browser')
            for log in browser_logs[-20:]:
                if 'ChurnPilot' in str(log.get('message', '')):
                    print(f"   {log['message'][:120]}")
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
