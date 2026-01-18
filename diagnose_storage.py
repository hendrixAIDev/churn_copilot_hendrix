"""Diagnostic tool to figure out why localStorage isn't working."""

import streamlit as st

st.title("ChurnPilot Storage Diagnostic")

st.markdown("""
This page will help diagnose why localStorage isn't persisting data.
""")

# Check 1: pyarrow
st.header("1. Check Dependencies")
try:
    import pyarrow
    st.success(f"✓ pyarrow installed: {pyarrow.__version__}")
except ImportError:
    st.error("✗ pyarrow NOT installed - localStorage won't work!")
    st.code("pip install pyarrow")

try:
    from streamlit_js_eval import streamlit_js_eval
    st.success("✓ streamlit-js-eval installed")
except ImportError:
    st.error("✗ streamlit-js-eval NOT installed")
    st.code("pip install streamlit-js-eval")

# Check 2: localStorage availability
st.header("2. Test localStorage")

if st.button("Test Write to localStorage"):
    try:
        from streamlit_js_eval import streamlit_js_eval

        test_value = "test_12345"
        js_code = f"""
        (function() {{
            try {{
                // Write test value
                localStorage.setItem('churnpilot_test', '{test_value}');

                // Read it back
                const value = localStorage.getItem('churnpilot_test');

                return {{
                    success: true,
                    written: '{test_value}',
                    read: value,
                    match: value === '{test_value}'
                }};
            }} catch (e) {{
                return {{
                    success: false,
                    error: e.message
                }};
            }}
        }})()
        """

        result = streamlit_js_eval(js=js_code, key="test_localstorage")

        if result and result.get('success'):
            if result.get('match'):
                st.success("✓ localStorage write/read works!")
                st.json(result)
            else:
                st.warning("⚠️ localStorage write succeeded but read mismatch")
                st.json(result)
        else:
            st.error("✗ localStorage failed")
            if result:
                st.json(result)
    except Exception as e:
        st.error(f"✗ Exception: {e}")

# Check 3: View current data
st.header("3. View Current localStorage Data")

if st.button("Check ChurnPilot Data"):
    try:
        from streamlit_js_eval import streamlit_js_eval

        js_code = """
        (function() {
            try {
                const data = localStorage.getItem('churnpilot_cards');
                if (data) {
                    const parsed = JSON.parse(data);
                    return {
                        found: true,
                        count: parsed.length,
                        size: data.length,
                        sample: parsed[0] ? parsed[0].name : null
                    };
                } else {
                    return {found: false};
                }
            } catch (e) {
                return {error: e.message};
            }
        })()
        """

        result = streamlit_js_eval(js=js_code, key="check_data")

        if result:
            if result.get('found'):
                st.success(f"✓ Found {result.get('count')} cards in localStorage")
                st.json(result)
            elif result.get('error'):
                st.error(f"✗ Error: {result.get('error')}")
            else:
                st.warning("No ChurnPilot data found in localStorage")
        else:
            st.warning("streamlit_js_eval returned None")
    except Exception as e:
        st.error(f"✗ Exception: {e}")

# Check 4: Browser info
st.header("4. Browser Information")

if st.button("Get Browser Info"):
    try:
        from streamlit_js_eval import streamlit_js_eval

        js_code = """
        (function() {
            return {
                userAgent: navigator.userAgent,
                cookieEnabled: navigator.cookieEnabled,
                language: navigator.language,
                onLine: navigator.onLine
            };
        })()
        """

        result = streamlit_js_eval(js=js_code, key="browser_info")
        if result:
            st.json(result)
    except Exception as e:
        st.error(f"Exception: {e}")

# Check 5: Session state
st.header("5. Session State")
st.write("Current session state:")
st.json({
    "cards_data": len(st.session_state.get('cards_data', [])),
    "storage_initialized": st.session_state.get('storage_initialized', False),
    "storage_type": st.session_state.get('storage_type', None)
})

# Check 6: Persistence Test (add test card)
st.header("6. Persistence Test")

col1, col2 = st.columns(2)

with col1:
    if st.button("Add Test Card to localStorage"):
        try:
            from streamlit_js_eval import streamlit_js_eval
            import time
            import json

            test_card = {
                "id": f"test-card-{int(time.time())}",
                "name": "Test Card for Persistence",
                "issuer": "Test Bank",
                "annual_fee": 0,
                "credits": [],
                "created_at": "2024-01-01T00:00:00"
            }

            # Get existing cards, add test card, save back
            js_code = f"""
            (function() {{
                try {{
                    let cards = [];
                    const existing = localStorage.getItem('churnpilot_cards');
                    if (existing) {{
                        cards = JSON.parse(existing);
                    }}

                    const testCard = {json.dumps(test_card)};
                    cards.push(testCard);

                    localStorage.setItem('churnpilot_cards', JSON.stringify(cards));

                    // Verify save
                    const saved = localStorage.getItem('churnpilot_cards');
                    const savedCards = JSON.parse(saved);

                    return {{
                        success: true,
                        totalCards: savedCards.length,
                        lastCard: savedCards[savedCards.length - 1].name
                    }};
                }} catch (e) {{
                    return {{success: false, error: e.message}};
                }}
            }})()
            """

            result = streamlit_js_eval(js=js_code, key=f"add_test_{time.time()}")

            if result and result.get('success'):
                st.success(f"✓ Added test card! Total: {result.get('totalCards')}")
                st.info("Now CLOSE this tab, reopen it, and click 'Check ChurnPilot Data' to verify persistence")
            else:
                st.error(f"✗ Failed: {result}")
        except Exception as e:
            st.error(f"✗ Exception: {e}")

with col2:
    if st.button("Clear All Test Data"):
        try:
            from streamlit_js_eval import streamlit_js_eval
            import time

            js_code = """
            (function() {
                try {
                    localStorage.removeItem('churnpilot_cards');
                    localStorage.removeItem('churnpilot_test');
                    return {success: true};
                } catch (e) {
                    return {success: false, error: e.message};
                }
            })()
            """

            result = streamlit_js_eval(js=js_code, key=f"clear_{time.time()}")

            if result and result.get('success'):
                st.success("✓ Cleared all ChurnPilot localStorage data")
            else:
                st.error(f"✗ Failed: {result}")
        except Exception as e:
            st.error(f"✗ Exception: {e}")

# Check 7: Automatic Load Test
st.header("7. Automatic Load on Page Load")
st.markdown("This section runs automatically to test if data loads on page load:")

try:
    from streamlit_js_eval import streamlit_js_eval
    import time

    # This runs automatically when page loads
    js_code = """
    (function() {
        try {
            const data = localStorage.getItem('churnpilot_cards');
            if (data) {
                const parsed = JSON.parse(data);
                return {
                    loaded: true,
                    count: parsed.length,
                    timestamp: new Date().toISOString()
                };
            } else {
                return {loaded: false, timestamp: new Date().toISOString()};
            }
        } catch (e) {
            return {error: e.message, timestamp: new Date().toISOString()};
        }
    })()
    """

    result = streamlit_js_eval(js=js_code, key=f"auto_load_{int(time.time())}")

    if result:
        if result.get('loaded'):
            st.success(f"✓ Auto-loaded {result.get('count')} cards at {result.get('timestamp')}")
        elif result.get('error'):
            st.error(f"✗ Error during auto-load: {result.get('error')}")
        else:
            st.info(f"No data found at {result.get('timestamp')}")
    else:
        st.warning("⚠️ streamlit_js_eval returned None - this might be a timing issue")
        st.info("Try refreshing the page")
except Exception as e:
    st.error(f"Auto-load exception: {e}")

# Recommendations
st.header("Recommendations")

st.markdown("""
**If localStorage tests pass:**
- Check if data is being saved after adding cards
- Look at browser console (F12) for errors
- Check Network tab for CORS issues

**If localStorage tests fail:**
- Install pyarrow: `pip install pyarrow`
- Check browser privacy settings
- Try in a different browser
- Check if third-party cookies are blocked

**If auto-load returns None:**
- This is a timing issue with streamlit-js-eval
- Refresh the page a few times
- The Promise-based approach in web_storage.py should handle this

**For pilot users on mobile/web:**
- localStorage is the ONLY option that works
- File-based storage won't work for web deployment
- Each user needs their own browser-based data

**Testing Persistence:**
1. Click "Add Test Card to localStorage"
2. CLOSE the browser tab completely
3. Reopen this page
4. Check if "7. Automatic Load on Page Load" shows your card
""")
