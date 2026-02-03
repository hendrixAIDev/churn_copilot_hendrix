"""Test script to verify query params session persistence works."""

import streamlit as st

st.set_page_config(page_title="Query Params Test", layout="wide")

st.title("Query Params Session Test")

st.markdown("""
This test verifies that query params work for session persistence:
1. **Set token** - Sets ?s=test_token_12345
2. **Read token** - Reads from query params
3. **Clear token** - Clears query params
4. **Refresh test** - Refresh the page to verify persistence
""")

# Current state
token = st.query_params.get("s")
st.write("**Current token in URL:**", token if token else "*None*")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Set Token", type="primary"):
        st.query_params["s"] = "test_token_12345"
        st.success("Token set! Check URL bar.")
        st.rerun()

with col2:
    if st.button("Clear Token"):
        st.query_params.clear()
        st.info("Token cleared! Check URL bar.")
        st.rerun()

with col3:
    if st.button("Read Token"):
        token = st.query_params.get("s")
        if token:
            st.success(f"Token found: {token}")
        else:
            st.warning("No token in URL")

st.divider()

st.markdown("""
### ✅ Testing Checklist

After clicking "Set Token":
1. URL should show `?s=test_token_12345`
2. Refresh page → Token should persist
3. Open new tab with same URL → Token should persist
4. Click "Clear Token" → URL should have no query params

**Expected behavior:**
- ✅ Same-tab refresh preserves token
- ✅ New tab with full URL preserves token
- ✅ Clear removes token from URL
""")
