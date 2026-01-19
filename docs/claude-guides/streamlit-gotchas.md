# Streamlit-Specific Gotchas

## 1. Tab Rendering Order (CRITICAL)

**Problem:**
- Streamlit renders ALL tab content in order on every rerun
- Dashboard (tab 1) renders BEFORE Add Card (tab 3) processes button clicks
- If button handler adds data, Dashboard already rendered with OLD data

**Result:** User adds card, switches to Dashboard, card not there!

**Solution:** MUST use `st.rerun()` after modifying data
```python
card = storage.add_card_from_template(...)
st.session_state.card_just_added = card.name
st.rerun()  # Forces fresh render with updated data
```

## 2. Session State vs Persistent Storage

**Session state:**
- In-memory only
- Lost on browser refresh
- Separate per tab/window

**Persistent storage (localStorage):**
- Survives browser restarts
- Shared across tabs
- Requires serialization

**Pattern:**
```python
if "cards_data" not in st.session_state:
    st.session_state.cards_data = load_from_storage()

# Work with session state, save to storage when changed
```

## 3. JavaScript Evaluation Timing

**Issue:** `streamlit-js-eval` can return None due to timing

**Root Cause:**
- JavaScript runs asynchronously in browser
- Python continues execution
- Result may not be ready when Python checks

**Solution:** Use simple synchronous JavaScript, not Promises
```python
# ✓ Good: Simple synchronous IIFE
js_code = """
(function() {
    try {
        var data = localStorage.getItem('key');
        if (data) return JSON.parse(data);
        return [];
    } catch (e) {
        return [];
    }
})()
"""
```

**Requirements:**
- Requires `pyarrow` to be installed
- Use SIMPLE synchronous JavaScript (no Promises)
- Handle None returns with retry logic

## 4. Widget State Persistence

**Problem:** Widget values don't persist across reruns unless using `key`

```python
# ❌ Bad: Value lost on rerun
card_name = st.text_input("Card Name")

# ✓ Good: Value persists
card_name = st.text_input("Card Name", key="card_name_input")
```

## 5. Deployment Context

**Web Deployment (Streamlit Cloud):**
- Server filesystem is ephemeral
- Must use browser localStorage
- Each user needs isolated data

**Desktop (localhost):**
- Can use file-based storage
- Single user

**Key insight:** Design for target deployment from the start.
