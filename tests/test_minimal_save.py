"""
Minimal test to verify streamlit_js_eval localStorage saving.
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

# Create a minimal Streamlit app for testing
MINIMAL_APP = """
import streamlit as st
from streamlit_js_eval import streamlit_js_eval, set_local_storage, get_local_storage

st.title("Minimal Save Test")

# Always try to load first
data = get_local_storage("test_key", component_key="load")
st.write(f"Loaded data: {data}")

if st.button("Save"):
    # Use a unique key each time
    import time
    save_key = f"save_{time.time()}"
    set_local_storage("test_key", "hello_world", component_key=save_key)
    st.success(f"Save component created (key={save_key})")
    # DON'T rerun - let the page complete

if st.button("Save and Rerun"):
    import time
    save_key = f"save_{time.time()}"
    set_local_storage("test_key", "hello_rerun", component_key=save_key)
    st.success("Save component created, will rerun...")
    st.rerun()

if st.button("Check localStorage"):
    st.rerun()
"""


def run_test():
    print("\n" + "="*60)
    print("Minimal Save Test")
    print("="*60 + "\n")

    # Write minimal app
    app_path = PROJECT_ROOT / "tests" / "_minimal_app.py"
    app_path.write_text(MINIMAL_APP)

    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["PYTHONUNBUFFERED"] = "1"

    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(app_path),
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

        initial = browser.execute_script("return localStorage.getItem('test_key')")
        print(f"   Initial localStorage: {initial}")

        # Step 2: Click "Save" button (no rerun)
        print("\n[Step 2] Click 'Save' button (no rerun)...")
        buttons = browser.find_elements(By.CSS_SELECTOR, "button")
        save_btn = None
        for btn in buttons:
            if btn.text.strip() == "Save":
                save_btn = btn
                break

        if save_btn:
            save_btn.click()
            print("   Clicked Save, waiting 5 seconds...")
            time.sleep(5)

            after_save = browser.execute_script("return localStorage.getItem('test_key')")
            print(f"   localStorage after Save: {after_save}")

            if after_save == "hello_world":
                print("   SUCCESS: Save without rerun works!")
            else:
                print("   FAIL: Save without rerun did not work")

        # Step 3: Clear and try "Save and Rerun"
        print("\n[Step 3] Clear and try 'Save and Rerun'...")
        browser.execute_script("localStorage.clear()")
        browser.refresh()
        time.sleep(8)

        buttons = browser.find_elements(By.CSS_SELECTOR, "button")
        save_rerun_btn = None
        for btn in buttons:
            if "Rerun" in btn.text:
                save_rerun_btn = btn
                break

        if save_rerun_btn:
            save_rerun_btn.click()
            print("   Clicked 'Save and Rerun', waiting 5 seconds...")
            time.sleep(5)

            after_save_rerun = browser.execute_script("return localStorage.getItem('test_key')")
            print(f"   localStorage after Save+Rerun: {after_save_rerun}")

            if after_save_rerun == "hello_rerun":
                print("   SUCCESS: Save with rerun works!")
            else:
                print("   FAIL: Save with rerun did not work")

                # Try clicking Check to trigger another render
                print("\n   Trying another refresh...")
                browser.refresh()
                time.sleep(5)
                after_check = browser.execute_script("return localStorage.getItem('test_key')")
                print(f"   localStorage after refresh: {after_check}")

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

        # Clean up
        app_path.unlink(missing_ok=True)
        print("\nApp stopped.")


if __name__ == "__main__":
    run_test()
