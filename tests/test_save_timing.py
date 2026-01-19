"""
Test to reproduce the save timing issue.
When adding a card and refreshing immediately, the new card should persist.
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
    print("Save Timing Test - Add Card and Refresh Immediately")
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
        time.sleep(8)
        browser.execute_script("localStorage.clear()")
        browser.refresh()
        time.sleep(8)

        initial = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   Initial localStorage: {initial}")

        # Step 2: Simulate adding a card by directly setting localStorage
        # (This simulates what the app should do when user adds a card)
        print("\n[Step 2] Add first card via localStorage...")
        card1 = {
            "id": "card-001",
            "name": "First Card",
            "issuer": "Bank A",
            "annual_fee": 0,
            "credits": [],
            "created_at": "2024-01-01T00:00:00"
        }
        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify([{json.dumps(card1)}]))"
        )
        after_add1 = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   After first card: {after_add1[:60] if after_add1 else 'None'}...")

        # Step 3: Refresh and check
        print("\n[Step 3] Refresh and check...")
        browser.refresh()
        time.sleep(8)
        after_refresh1 = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   After refresh: {after_refresh1[:60] if after_refresh1 else 'None'}...")

        if after_refresh1:
            cards = json.loads(after_refresh1)
            print(f"   Card count: {len(cards)}")

        # Step 4: Add second card
        print("\n[Step 4] Add second card...")
        cards = json.loads(browser.execute_script("return localStorage.getItem('churnpilot_cards')") or '[]')
        card2 = {
            "id": "card-002",
            "name": "Second Card",
            "issuer": "Bank B",
            "annual_fee": 95,
            "credits": [],
            "created_at": "2024-01-02T00:00:00"
        }
        cards.append(card2)
        browser.execute_script(
            f"localStorage.setItem('churnpilot_cards', JSON.stringify({json.dumps(cards)}))"
        )
        after_add2 = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        print(f"   After second card: {len(json.loads(after_add2))} cards")

        # Step 5: IMMEDIATE refresh (simulating user behavior)
        print("\n[Step 5] IMMEDIATE refresh (0.5 second delay)...")
        time.sleep(0.5)  # Very short delay
        browser.refresh()
        time.sleep(8)

        after_immediate = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
        if after_immediate:
            cards_after = json.loads(after_immediate)
            print(f"   After immediate refresh: {len(cards_after)} cards")
            if len(cards_after) == 2:
                print("   SUCCESS: Both cards persisted!")
            else:
                print(f"   FAIL: Expected 2 cards, got {len(cards_after)}")
                print(f"   Cards: {[c['name'] for c in cards_after]}")
        else:
            print("   FAIL: localStorage is empty!")

        # Step 6: Now test the ACTUAL app behavior
        print("\n[Step 6] Testing actual app save behavior...")
        print("   Clearing localStorage and navigating to Add Card...")
        browser.execute_script("localStorage.clear()")
        browser.refresh()
        time.sleep(10)

        # Try to find and click the Add Card tab
        try:
            tabs = browser.find_elements(By.CSS_SELECTOR, "[data-baseweb='tab']")
            for tab in tabs:
                if "Add" in tab.text:
                    tab.click()
                    time.sleep(2)
                    print(f"   Clicked: {tab.text}")
                    break

            # Look for the card library dropdown
            time.sleep(2)

            # Check what's in localStorage after interacting with the app
            ls_after_interaction = browser.execute_script("return localStorage.getItem('churnpilot_cards')")
            print(f"   localStorage after interaction: {ls_after_interaction[:60] if ls_after_interaction else 'None'}")

        except Exception as e:
            print(f"   Could not interact with app: {e}")

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
        print("\nApp stopped.")


if __name__ == "__main__":
    run_test()
