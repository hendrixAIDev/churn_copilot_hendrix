# ChurnPilot Session Persistence Investigation Report
**Date:** 2026-02-02  
**Agent:** Sub-agent (churnpilot-deep-fix)  
**Status:** ⚠️ Root causes identified, partial fixes applied, localStorage writes still not executing

---

## Executive Summary

**Problem:** Session tokens were NOT persisting at all. Both same-tab refresh AND new tab navigation logged users out immediately.

**Root Causes Identified:**
1. ✅ **FIXED**: Stable key caching - `_load_session_token()` used a stable key (`"session_loader"`) that cached the first None result and never re-read from localStorage
2. ⚠️ **PARTIALLY FIXED**: streamlit_js_eval component execution timing - Components are created but never execute before page reruns

**Current Status:**
- Same-tab refresh: ✅ Works (using Streamlit's built-in session persistence, NOT localStorage)
- New tab navigation: ❌ Still broken (localStorage never written to)
- Direct URL access: ❌ Still broken (localStorage never written to)

---

## Investigation Findings

### 1. localStorage Functionality Test

**Test Setup:** Created `test_localstorage.py` - minimal Streamlit app to test streamlit_js_eval + localStorage integration.

**Results:**
- ✅ **Write to localStorage:** WORKS - Console shows `[Test] Write successful: test_session_12345`
- ✅ **Read from localStorage:** WORKS - Console shows `[Test] Read result: test_session_12345`
- ✅ **window.parent.localStorage access:** WORKS - streamlit_js_eval successfully bypasses iframe sandbox

**Conclusion:** localStorage and streamlit_js_eval work perfectly. The issue is in the application flow.

---

### 2. Root Cause #1: Stable Key Caching

**Problem Location:** `src/ui/app.py`, line ~665

**Original Code:**
```python
def _load_session_token() -> str | None:
    # Use stable key so streamlit_js_eval caches the result across reruns
    result = streamlit_js_eval(js_expressions=js_code, key="session_loader")
    return result
```

**Why It Failed:**
- First render: Component mounts, returns `None` (localStorage not checked yet)
- streamlit_js_eval caches this `None` result under key `"session_loader"`
- All subsequent reruns: Returns cached `None`, never actually reads localStorage
- Even after writing to localStorage, the cached `None` persists

**Fix Applied:**
```python
def _load_session_token() -> str | None:
    # Use the rerun attempt flag as part of the key to distinguish Phase 1 from Phase 2
    # This prevents caching the initial None result across the rerun
    attempt = "phase2" if st.session_state.get("_session_check_rerun_attempted") else "phase1"
    
    result = streamlit_js_eval(
        js_expressions=js_code,
        key=f"session_load_{attempt}"
    )
    return result
```

**Status:** ✅ FIXED - Phase 1 and Phase 2 now use different keys, preventing stale None caching

---

### 3. Root Cause #2: Component Execution Timing

**Problem Location:** `src/ui/app.py`, registration and login flows

**Original Code (Registration):**
```python
user = auth.register(email, password)
token = auth.create_session(user.id)
st.session_state.user_id = str(user.id)
st.session_state.user_email = user.email
st.session_state.session_token = token
_save_session_token(token)  # Creates streamlit_js_eval component
st.success("Account created! Redirecting...")
st.rerun()  # ← IMMEDIATELY reruns, killing the component before it executes
```

**Why It Failed:**
1. `_save_session_token(token)` creates a streamlit_js_eval component but doesn't execute it yet
2. `st.rerun()` is called immediately after
3. The page reruns BEFORE the component's JavaScript can execute
4. Component is destroyed, localStorage never written to
5. On the rerun, user appears logged in (session_state has the data), but localStorage is empty

**Same Issue in Login Flow:** Identical pattern at line ~820

**Fix Attempted:**
```python
# Registration flow - removed immediate rerun
user = auth.register(email, password)
token = auth.create_session(user.id)
st.session_state.user_id = str(user.id)
st.session_state.user_email = user.email
st.session_state.session_token = token
_save_session_token(token)  # Component created
st.session_state._auth_success = True  # Flag for delayed rerun
st.success("Account created! Redirecting...")
# No immediate rerun - let component execute first
```

**Delayed Rerun Trigger:**
Added at end of `show_auth_page()`:
```python
# Trigger rerun after localStorage save component has executed
if st.session_state.get("_auth_success"):
    del st.session_state._auth_success
    st.rerun()
```

**Status:** ⚠️ PARTIALLY WORKS
- Same-tab refresh now works (but relies on Streamlit session persistence, NOT localStorage)
- localStorage writes still don't execute (component timing issue persists)
- Browser console shows NO "[ChurnPilot] Session token saved to localStorage" messages
- Manual check: `window.parent.localStorage.getItem('churnpilot_session')` returns `null`

---

## Why Same-Tab Refresh Works (But It's NOT localStorage)

When you refresh the same tab, Streamlit has **built-in session state persistence** that survives refreshes within the same browser tab. This is NOT the localStorage-based persistence we're implementing. Evidence:

1. After registration, localStorage is empty: `window.parent.localStorage.getItem('churnpilot_session')` → `null`
2. But refresh still keeps you logged in
3. This is Streamlit's session cookie/state persistence, NOT our localStorage implementation

**The Problem:** Opening a new tab or navigating directly to the URL will still log you out because localStorage was never written to.

---

## Remaining Issues

### Issue #1: streamlit_js_eval Component Never Executes

**Theory:** Even with the delayed rerun approach, the component isn't executing because:
- The component is created during form submission
- Streamlit re-renders the page after form submission
- The component gets recreated/destroyed before it can execute

**Possible Solutions:**
1. **Render the component OUTSIDE the form** - Create it in a persistent location that doesn't get recreated on form submit
2. **Use st.experimental_rerun() instead of st.rerun()** - May give components more time
3. **Add explicit delay before rerun** - `time.sleep(0.5)` before rerun (not ideal, but may work)
4. **Alternative: Use cookies** - Switch from localStorage to server-set cookies (more reliable but less elegant)
5. **Alternative: Accept the limitation** - Document that localStorage persistence only works after the second page load (first load writes, second load reads)

### Issue #2: No Component Execution Confirmation

The browser console never shows:
- `[ChurnPilot] Session token saved to localStorage`

This confirms the component's JavaScript never runs.

---

## Files Modified

1. **`src/ui/app.py`**:
   - Fixed `_load_session_token()` - Changed from stable key to phase-based keys
   - Modified registration flow - Removed immediate `st.rerun()`, added `_auth_success` flag
   - Modified login flow - Same changes as registration
   - Added delayed rerun trigger at end of `show_auth_page()`

2. **`test_localstorage.py`** (NEW):
   - Comprehensive test script for localStorage functionality
   - Confirms streamlit_js_eval + localStorage works correctly
   - Used to isolate the problem from application flow

---

## Next Steps (Recommended)

### Option A: Force Component Execution (Preferred)
1. Move `_save_session_token()` call to a location that persists across reruns
2. Use a session_state flag to track if save was attempted
3. Only trigger rerun after confirming component executed (check for non-None return value)

### Option B: Alternative Persistence Method
1. Switch to server-set HTTP cookies instead of localStorage
2. More reliable, works across all scenarios
3. Downside: Slightly less elegant, requires server-side cookie management

### Option C: Accept Two-Phase Save
1. Save to localStorage happens on SECOND page interaction (not first)
2. Document this behavior
3. User stays logged in on first session via Streamlit session state
4. localStorage persistence kicks in after first card add/navigation

---

## Testing Checklist

To verify a fix works:
1. ✅ Create a new account
2. ✅ Check browser console for `[ChurnPilot] Session token saved to localStorage`
3. ✅ Run: `window.parent.localStorage.getItem('churnpilot_session')` → Should return a 64-char hex string
4. ✅ Refresh the same tab → Should stay logged in
5. ✅ Open a new tab, navigate to URL → Should stay logged in
6. ✅ Close browser, reopen, navigate to URL → Should stay logged in (if session not expired)

**Current Status:**
- Step 1: ✅ Works
- Step 2: ❌ Message never appears
- Step 3: ❌ Returns `null`
- Step 4: ✅ Works (but using Streamlit session persistence, not localStorage)
- Step 5: ❌ Not tested (would fail due to empty localStorage)
- Step 6: ❌ Not tested (would fail due to empty localStorage)

---

## Technical Notes

### streamlit_js_eval Two-Phase Pattern

streamlit_js_eval components execute asynchronously:
- **Phase 1 (First Render):** Component mounts, returns `None`
- **Phase 2 (After Mount):** Component executes JavaScript, returns actual value

This is why the code uses:
```python
if token is None:
    if not st.session_state.get("_session_check_rerun_attempted"):
        st.session_state._session_check_rerun_attempted = True
        st.rerun()  # Trigger Phase 2
```

### Why Incrementing Counters Don't Work for Reads

Using an incrementing counter for `_load_session_token()` would cause:
1. First render: Create component with key `session_load_1`, returns None
2. Trigger rerun
3. Second render: Create NEW component with key `session_load_2`, returns None again (Phase 1)
4. Infinite loop of reruns

Solution: Use a flag-based key that changes only ONCE (phase1 → phase2).

---

## Conclusion

**What Works:**
- localStorage read/write functionality ✅
- Phase-based key system prevents stale caching ✅
- Same-tab refresh (via Streamlit session state) ✅

**What Doesn't Work:**
- localStorage writes never execute ❌
- New tab persistence ❌
- Direct URL navigation persistence ❌

**Root Cause:** streamlit_js_eval save components are created but destroyed before JavaScript execution due to Streamlit's rendering lifecycle during form submissions.

**Recommended Fix:** Implement Option A (force component execution) or Option B (switch to cookies).
