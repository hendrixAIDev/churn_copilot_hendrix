"""Minimal localStorage diagnostic to understand the exact failure point."""

import streamlit as st
import json
from streamlit.components.v1 import html

st.set_page_config(page_title="localStorage Debug", page_icon="🔍")

st.title("🔍 Minimal localStorage Debug")

# Test 1: Can we write to localStorage using HTML injection?
st.header("Test 1: HTML Injection Write")

test_data = {"test_key": "test_value", "timestamp": str(st.session_state.get('counter', 0))}

if st.button("Write via HTML injection"):
    data_json = json.dumps(test_data)
    # Escape for JS string
    data_escaped = data_json.replace('\\', '\\\\').replace("'", "\\'")

    script = f"""
    <script>
    (function() {{
        try {{
            localStorage.setItem('debug_test', '{data_escaped}');
            console.log('[DEBUG] Wrote to localStorage:', '{data_escaped}');
            // Also write to a visible element to confirm script ran
            document.body.setAttribute('data-save-status', 'saved');
        }} catch (e) {{
            console.error('[DEBUG] Write error:', e);
        }}
    }})();
    </script>
    <div id="save-status">Script injected</div>
    """

    html(script, height=30)
    st.success("HTML injected - check browser console (F12)")

# Test 2: Can we read from localStorage using streamlit_js_eval?
st.header("Test 2: streamlit_js_eval Read")

try:
    from streamlit_js_eval import streamlit_js_eval

    if st.button("Read via streamlit_js_eval"):
        js_code = """
        (function() {
            try {
                var data = localStorage.getItem('debug_test');
                console.log('[DEBUG] Read from localStorage:', data);
                return data;
            } catch (e) {
                console.error('[DEBUG] Read error:', e);
                return 'ERROR: ' + e.message;
            }
        })()
        """

        # Use unique key to avoid caching
        import time
        result = streamlit_js_eval(js=js_code, key=f"read_{time.time()}")

        st.write(f"**Result type:** {type(result)}")
        st.write(f"**Result value:** {result}")

        if result is None:
            st.error("❌ streamlit_js_eval returned None - timing issue!")
        elif result.startswith('ERROR'):
            st.error(f"❌ JavaScript error: {result}")
        else:
            st.success(f"✓ Read succeeded: {result}")

except ImportError as e:
    st.error(f"streamlit_js_eval not installed: {e}")

# Test 3: Alternative - use streamlit_js_eval for BOTH read and write
st.header("Test 3: streamlit_js_eval Write + Read")

if st.button("Write AND Read via streamlit_js_eval"):
    try:
        from streamlit_js_eval import streamlit_js_eval
        import time

        write_js = f"""
        (function() {{
            try {{
                var testData = {json.dumps(test_data)};
                localStorage.setItem('debug_test_v2', JSON.stringify(testData));
                var verify = localStorage.getItem('debug_test_v2');
                return {{
                    wrote: testData,
                    verified: verify,
                    match: verify === JSON.stringify(testData)
                }};
            }} catch (e) {{
                return {{error: e.message}};
            }}
        }})()
        """

        result = streamlit_js_eval(js=write_js, key=f"write_read_{time.time()}")

        st.write(f"**Result:** {result}")

        if result is None:
            st.error("❌ streamlit_js_eval returned None")
        elif isinstance(result, dict) and result.get('error'):
            st.error(f"❌ Error: {result['error']}")
        elif isinstance(result, dict) and result.get('match'):
            st.success("✓ Write + verify succeeded!")
        else:
            st.warning(f"⚠️ Unexpected result: {result}")

    except Exception as e:
        st.error(f"Exception: {e}")

# Test 4: Check current localStorage state
st.header("Test 4: Read All ChurnPilot Keys")

if st.button("Check all churnpilot_* keys"):
    try:
        from streamlit_js_eval import streamlit_js_eval
        import time

        js_code = """
        (function() {
            var result = {};
            for (var i = 0; i < localStorage.length; i++) {
                var key = localStorage.key(i);
                if (key.startsWith('churnpilot') || key.startsWith('debug')) {
                    result[key] = localStorage.getItem(key);
                }
            }
            return result;
        })()
        """

        result = streamlit_js_eval(js=js_code, key=f"all_keys_{time.time()}")

        if result is None:
            st.error("❌ streamlit_js_eval returned None")
        elif isinstance(result, dict):
            if len(result) == 0:
                st.info("No churnpilot_* or debug_* keys found in localStorage")
            else:
                st.success(f"Found {len(result)} keys:")
                for key, value in result.items():
                    with st.expander(key):
                        try:
                            parsed = json.loads(value)
                            st.json(parsed)
                        except:
                            st.text(value)
        else:
            st.warning(f"Unexpected: {result}")

    except Exception as e:
        st.error(f"Exception: {e}")

# Test 5: Alternative save method using larger iframe
st.header("Test 5: HTML Injection with visible iframe")

if st.button("Write via visible HTML iframe"):
    data_json = json.dumps(test_data)
    data_escaped = data_json.replace('\\', '\\\\').replace("'", "\\'")

    script = f"""
    <div id="status" style="padding: 10px; background: #f0f0f0; border-radius: 5px;">
        <script>
        (function() {{
            try {{
                localStorage.setItem('debug_test_visible', '{data_escaped}');
                document.getElementById('status').innerHTML = '✓ Saved to localStorage!';
                document.getElementById('status').style.background = '#d4edda';
            }} catch (e) {{
                document.getElementById('status').innerHTML = '❌ Error: ' + e.message;
                document.getElementById('status').style.background = '#f8d7da';
            }}
        }})();
        </script>
        Running...
    </div>
    """

    html(script, height=50)

st.divider()
st.caption("Instructions: Run tests 1-5 in order, check browser console (F12) for logs.")
st.caption("If Test 1 shows 'Script injected' but Test 2 returns None, the issue is with streamlit_js_eval reading.")
st.caption("If Test 5 doesn't show '✓ Saved', the issue is with HTML/iframe execution.")
