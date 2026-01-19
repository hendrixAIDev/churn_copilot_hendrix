"""
PERSISTENCE DIAGNOSTIC TOOL
============================
Run this to diagnose why localStorage isn't persisting.

Usage: streamlit run diagnose_persistence.py

This tool tests each step of the save/load process to identify
exactly where the failure occurs.
"""

import streamlit as st
import json
import time

st.set_page_config(page_title="Persistence Diagnostic", page_icon="🔍", layout="wide")

st.title("🔍 Persistence Diagnostic")
st.caption("This tool identifies exactly where localStorage persistence fails.")

# Initialize
if "test_counter" not in st.session_state:
    st.session_state.test_counter = 0

# Check dependencies first
st.header("Step 1: Check Dependencies")

col1, col2 = st.columns(2)

with col1:
    try:
        import pyarrow
        st.success(f"✅ pyarrow: {pyarrow.__version__}")
    except ImportError:
        st.error("❌ pyarrow NOT installed")
        st.code("pip install pyarrow")
        st.stop()

with col2:
    try:
        from streamlit_js_eval import streamlit_js_eval
        st.success("✅ streamlit-js-eval installed")
    except ImportError:
        st.error("❌ streamlit-js-eval NOT installed")
        st.code("pip install streamlit-js-eval")
        st.stop()

st.divider()

# Test 2: Basic JS execution
st.header("Step 2: Test JavaScript Execution")

if st.button("Test basic JS execution", key="test_js"):
    from streamlit_js_eval import streamlit_js_eval

    result = streamlit_js_eval(
        js_expressions="1 + 1",
        key=f"basic_js_{time.time()}"
    )

    if result == 2:
        st.success(f"✅ Basic JS works! Result: {result}")
    elif result is None:
        st.error("❌ JS returned None - timing issue")
        st.info("Try clicking the button again")
    else:
        st.warning(f"⚠️ Unexpected result: {result}")

st.divider()

# Test 3: localStorage read
st.header("Step 3: Test localStorage Read")

st.markdown("**Check what's currently in localStorage:**")

if st.button("Read localStorage", key="read_ls"):
    from streamlit_js_eval import streamlit_js_eval

    js_code = """
    (function() {
        try {
            var keys = [];
            for (var i = 0; i < localStorage.length; i++) {
                var key = localStorage.key(i);
                if (key.startsWith('churnpilot') || key.startsWith('test_')) {
                    keys.push({
                        key: key,
                        value: localStorage.getItem(key),
                        size: localStorage.getItem(key).length
                    });
                }
            }
            return {success: true, keys: keys, total: localStorage.length};
        } catch (e) {
            return {success: false, error: e.message};
        }
    })()
    """

    result = streamlit_js_eval(js=js_code, key=f"read_ls_{time.time()}")

    if result is None:
        st.error("❌ streamlit_js_eval returned None")
        st.info("This is a timing issue. Try clicking again.")
    elif result.get('success'):
        st.success(f"✅ localStorage accessible! Total keys: {result.get('total')}")
        if result.get('keys'):
            for item in result.get('keys'):
                with st.expander(f"📦 {item['key']} ({item['size']} bytes)"):
                    try:
                        parsed = json.loads(item['value'])
                        st.json(parsed)
                    except:
                        st.text(item['value'][:500])
        else:
            st.info("No churnpilot_* or test_* keys found")
    else:
        st.error(f"❌ Error: {result.get('error')}")

st.divider()

# Test 4: localStorage write with verification
st.header("Step 4: Test localStorage Write")

st.markdown("**This is the critical test - can we write AND verify?**")

test_data = {"test_id": str(time.time()), "message": "Test data", "counter": st.session_state.test_counter}

if st.button("Write to localStorage", key="write_ls"):
    from streamlit_js_eval import streamlit_js_eval

    st.session_state.test_counter += 1
    test_data["counter"] = st.session_state.test_counter

    # Write AND immediately verify in same JS call
    js_code = f"""
    (function() {{
        try {{
            var testData = {json.dumps(test_data)};

            // Write
            localStorage.setItem('test_persistence', JSON.stringify(testData));

            // Immediately verify
            var readBack = localStorage.getItem('test_persistence');
            var parsed = JSON.parse(readBack);

            return {{
                success: true,
                wrote: testData,
                readBack: parsed,
                match: JSON.stringify(testData) === readBack
            }};
        }} catch (e) {{
            return {{success: false, error: e.message}};
        }}
    }})()
    """

    result = streamlit_js_eval(js=js_code, key=f"write_ls_{time.time()}")

    if result is None:
        st.error("❌ streamlit_js_eval returned None")
        st.warning("**This is likely why persistence fails!**")
        st.info("The JavaScript may not be executing reliably.")
    elif result.get('success') and result.get('match'):
        st.success("✅ Write + immediate verify succeeded!")
        st.json(result)
    elif result.get('success'):
        st.warning("⚠️ Write succeeded but verify failed")
        st.json(result)
    else:
        st.error(f"❌ Error: {result.get('error')}")

st.divider()

# Test 5: Write then read separately
st.header("Step 5: Test Write → Refresh → Read")

st.markdown("""
**This tests actual persistence:**
1. Click "Write test data"
2. **Refresh the page (F5)**
3. Click "Read test data"
4. If data is there, persistence works!
""")

col1, col2 = st.columns(2)

with col1:
    if st.button("Write test data", key="write_persist"):
        from streamlit_js_eval import streamlit_js_eval

        persist_data = {
            "timestamp": time.time(),
            "message": "If you see this after refresh, persistence works!",
            "random": st.session_state.test_counter
        }
        st.session_state.test_counter += 1

        js_code = f"""
        (function() {{
            try {{
                localStorage.setItem('test_persist_check', JSON.stringify({json.dumps(persist_data)}));
                console.log('[Diagnostic] Wrote test data');
                return true;
            }} catch (e) {{
                return {{error: e.message}};
            }}
        }})()
        """

        result = streamlit_js_eval(js=js_code, key=f"write_persist_{time.time()}")

        if result is True:
            st.success("✅ Write command sent")
            st.warning("**Now refresh the page (F5) and click 'Read test data'**")
        elif result is None:
            st.error("❌ JS returned None - write may have failed")
        else:
            st.error(f"❌ Error: {result}")

with col2:
    if st.button("Read test data", key="read_persist"):
        from streamlit_js_eval import streamlit_js_eval

        js_code = """
        (function() {
            try {
                var data = localStorage.getItem('test_persist_check');
                if (data) {
                    return JSON.parse(data);
                }
                return null;
            } catch (e) {
                return {error: e.message};
            }
        })()
        """

        result = streamlit_js_eval(js=js_code, key=f"read_persist_{time.time()}")

        if result is None:
            st.warning("⚠️ No data found (or JS returned None)")
            st.info("If you just refreshed and see this, persistence is NOT working.")
        elif isinstance(result, dict) and 'error' in result:
            st.error(f"❌ Error: {result['error']}")
        else:
            st.success("✅ Data persisted!")
            st.json(result)

st.divider()

# Test 6: Alternative save method using HTML
st.header("Step 6: Alternative - HTML Component Save")

st.markdown("**Testing if st.components.v1.html works better:**")

if st.button("Save via HTML component", key="html_save"):
    from streamlit.components.v1 import html

    html_data = {
        "method": "html_component",
        "timestamp": time.time(),
        "counter": st.session_state.test_counter
    }
    st.session_state.test_counter += 1

    # Use a visible component to ensure execution
    save_html = f"""
    <div id="save-status" style="padding: 10px; background: #f0f0f0; border-radius: 5px; font-family: monospace;">
        <script>
        (function() {{
            try {{
                var data = {json.dumps(html_data)};
                localStorage.setItem('test_html_save', JSON.stringify(data));
                document.getElementById('save-status').innerHTML = '✅ Saved via HTML: ' + JSON.stringify(data);
                document.getElementById('save-status').style.background = '#d4edda';
                console.log('[Diagnostic] HTML save succeeded');
            }} catch (e) {{
                document.getElementById('save-status').innerHTML = '❌ Error: ' + e.message;
                document.getElementById('save-status').style.background = '#f8d7da';
            }}
        }})();
        </script>
        ⏳ Executing save...
    </div>
    """

    html(save_html, height=60)
    st.info("Check if the box above shows '✅ Saved'. Then refresh and use 'Read localStorage' to verify.")

st.divider()

# Summary
st.header("📋 Diagnostic Summary")

st.markdown("""
**If Step 4 returns None frequently:**
- `streamlit_js_eval` has timing issues
- Need alternative approach

**If Step 5 data doesn't persist after refresh:**
- localStorage write is not executing
- Try the HTML component method (Step 6)

**If Step 6 HTML shows '✅ Saved' but data still disappears:**
- Browser might be blocking localStorage
- Check browser privacy settings
- Try in non-incognito mode

**Report these results** to help diagnose the issue.
""")

# Browser info
st.divider()
st.header("🌐 Browser Information")

try:
    from streamlit_js_eval import streamlit_js_eval

    browser_info = streamlit_js_eval(
        js_expressions="""
        {
            userAgent: navigator.userAgent.substring(0, 100),
            cookiesEnabled: navigator.cookieEnabled,
            localStorageAvailable: typeof localStorage !== 'undefined'
        }
        """,
        key="browser_info"
    )

    if browser_info:
        st.json(browser_info)
    else:
        st.warning("Could not get browser info (JS returned None)")
except Exception as e:
    st.error(f"Error: {e}")
