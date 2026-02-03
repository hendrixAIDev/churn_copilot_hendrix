"""Minimal test for streamlit_js_eval + localStorage integration.

This script tests:
1. If streamlit_js_eval can write to window.parent.localStorage
2. If streamlit_js_eval can read from window.parent.localStorage
3. The two-phase loading pattern (None on first render, value on rerun)

Run with: streamlit run test_localstorage.py
"""

import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="localStorage Test", layout="centered")

st.title("🧪 localStorage Test")
st.markdown("---")

# Initialize counters
if "phase_counter" not in st.session_state:
    st.session_state.phase_counter = 0
if "write_counter" not in st.session_state:
    st.session_state.write_counter = 0
if "read_counter" not in st.session_state:
    st.session_state.read_counter = 0

st.session_state.phase_counter += 1

st.info(f"🔄 Page render #{st.session_state.phase_counter}")

st.markdown("## Test 1: Write to localStorage")

test_value = st.text_input("Test value to write:", value="test_session_12345", key="test_input")

if st.button("Write to localStorage", type="primary"):
    st.session_state.write_counter += 1
    
    js_code = f"""
    (function() {{
        try {{
            console.log('[Test] Writing to localStorage...');
            window.parent.localStorage.setItem('churnpilot_test', '{test_value}');
            console.log('[Test] Write successful:', '{test_value}');
            return true;
        }} catch (e) {{
            console.error('[Test] Write error:', e);
            return false;
        }}
    }})()
    """
    
    result = streamlit_js_eval(
        js_expressions=js_code,
        key=f"write_test_{st.session_state.write_counter}"
    )
    
    st.success(f"✓ Write initiated (result: {result})")
    st.caption("Check browser console for '[Test] Write successful' message")

st.markdown("---")
st.markdown("## Test 2: Read from localStorage")

if st.button("Read from localStorage", type="primary"):
    st.session_state.read_counter += 1
    
    js_code = """
    (function() {
        try {
            console.log('[Test] Reading from localStorage...');
            var value = window.parent.localStorage.getItem('churnpilot_test');
            console.log('[Test] Read result:', value);
            return value || null;
        } catch (e) {
            console.error('[Test] Read error:', e);
            return null;
        }
    })()
    """
    
    result = streamlit_js_eval(
        js_expressions=js_code,
        key=f"read_test_{st.session_state.read_counter}"
    )
    
    if result is None:
        st.warning("⚠️ Result is None - this is expected on first render. Click 'Read from localStorage' again.")
        st.caption("streamlit_js_eval returns None on first render (component mounting phase)")
    else:
        st.success(f"✓ Read successful: '{result}'")

st.markdown("---")
st.markdown("## Test 3: Two-Phase Loading Pattern")

if "two_phase_rerun" not in st.session_state:
    st.session_state.two_phase_rerun = False

if st.button("Test Two-Phase Pattern"):
    st.session_state.two_phase_rerun = False
    st.session_state.read_counter += 1

js_code_two_phase = """
(function() {
    try {
        var value = window.parent.localStorage.getItem('churnpilot_test');
        console.log('[Two-Phase Test] Read:', value);
        return value || null;
    } catch (e) {
        console.error('[Two-Phase Test] Error:', e);
        return null;
    }
})()
"""

result_two_phase = streamlit_js_eval(
    js_expressions=js_code_two_phase,
    key="two_phase_stable"
)

if result_two_phase is None:
    if not st.session_state.two_phase_rerun:
        st.warning("Phase 1: streamlit_js_eval returned None (component mounting). Triggering rerun...")
        st.session_state.two_phase_rerun = True
        st.rerun()
    else:
        st.error("❌ Phase 2: Still None after rerun - localStorage may be empty or inaccessible")
else:
    st.success(f"✅ Phase 2: Got value after rerun: '{result_two_phase}'")
    st.session_state.two_phase_rerun = False

st.markdown("---")
st.markdown("## Test 4: Manual Browser Check")
st.markdown("""
Open browser DevTools Console (F12 or Cmd+Opt+I) and run:

```javascript
window.parent.localStorage.getItem('churnpilot_test')
```

This will show you if the value is actually in localStorage.
""")

st.markdown("---")
st.markdown("## Test 5: Clear localStorage")

if st.button("Clear Test Data", type="secondary"):
    st.session_state.write_counter += 1
    
    js_code = """
    (function() {
        try {
            window.parent.localStorage.removeItem('churnpilot_test');
            console.log('[Test] Cleared localStorage');
            return true;
        } catch (e) {
            console.error('[Test] Clear error:', e);
            return false;
        }
    })()
    """
    
    result = streamlit_js_eval(
        js_expressions=js_code,
        key=f"clear_test_{st.session_state.write_counter}"
    )
    
    st.info("Cleared test data from localStorage")

st.markdown("---")
st.markdown("## Session State Debug")
with st.expander("View session state"):
    st.json({
        "phase_counter": st.session_state.phase_counter,
        "write_counter": st.session_state.write_counter,
        "read_counter": st.session_state.read_counter,
        "two_phase_rerun": st.session_state.two_phase_rerun,
    })
