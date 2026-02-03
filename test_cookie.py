"""Test if CookieManager works with Streamlit."""

import streamlit as st
from extra_streamlit_components import CookieManager

st.set_page_config(page_title="Cookie Test", layout="centered")

st.title("🍪 Cookie Test")

# Initialize cookie manager
cookie_manager = CookieManager()

# Get all cookies
all_cookies = cookie_manager.get_all()
st.write("**All cookies:**", all_cookies)

# Test setting a cookie
if st.button("Set Test Cookie"):
    cookie_manager.set("test_token", "abc123_test_value", expires_at=None)
    st.success("Cookie set! Refresh the page to verify persistence.")
    st.rerun()

# Test reading the cookie
test_cookie = cookie_manager.get("test_token")
st.write("**test_token cookie:**", test_cookie)

# Test clearing
if st.button("Clear Test Cookie"):
    cookie_manager.delete("test_token")
    st.success("Cookie cleared!")
    st.rerun()

st.markdown("---")
st.markdown("""
**Test procedure:**
1. Click "Set Test Cookie"
2. Close this tab completely
3. Open a fresh tab with just the URL (no query params)
4. If the cookie persists, CookieManager works for session persistence!
""")
