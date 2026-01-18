# ChurnPilot - Testing & Verification Guide

## Recent Fixes (2026-01-18)

### Bugs Fixed
1. **Tab switching bug** - Clicking card in library no longer redirects to Dashboard
2. **Data persistence** - Cards now persist after closing browser

### How to Test

#### Test 1: Tab Switching Fix

**Steps:**
1. Start Streamlit: `streamlit run src/ui/app.py`
2. Go to "Add Card" tab
3. Select a card from library (e.g., Amex Platinum)
4. Fill in details and click "Add Card"

**Expected:**
- ✓ Success message appears
- ✓ Page STAYS on "Add Card" tab (doesn't switch to Dashboard)
- ✓ Info message: "Switch to Dashboard tab to see your card"

**Actual Result:**
- Before fix: Would jump to Dashboard tab immediately
- After fix: Stays on Add Card tab

---

#### Test 2: Data Persistence

**Steps:**
1. Add a card from library
2. Switch to Dashboard - card should appear
3. **Close the browser completely** (not just the tab)
4. Reopen browser and navigate to the app
5. Check Dashboard

**Expected:**
- ✓ Card should still be there
- ✓ File exists at: `C:\Users\JayCh\.churnpilot\cards.json`

**How to verify the file:**
```bash
# Check if file exists
ls ~\.churnpilot\cards.json

# View contents
cat ~\.churnpilot\cards.json

# Or in Python
python -c "import json; from pathlib import Path; print(json.load(open(Path.home() / '.churnpilot' / 'cards.json')))"
```

---

#### Test 3: Automated Test

**Run the test script:**
```bash
python test_hybrid_storage.py
```

**Expected output:**
```
[OK] File is readable
[OK] Contains X cards
[OK] Initialized storage
[OK] Added test card
[OK] File contains X cards
[OK] Test card found in file!
```

**If test passes:**
- Storage is working correctly
- File-based persistence is functional
- Data will survive browser restarts

---

## How Data Persistence Works Now

### Hybrid Storage System

The app uses **HybridStorage** which combines two methods:

1. **localStorage** (in browser)
   - Fast, browser-based storage
   - Data survives page refreshes
   - May not work in incognito/private mode
   - Requires `streamlit-js-eval` + `pyarrow`

2. **File backup** (on disk)
   - **Always saves here**: `~/.churnpilot/cards.json`
   - Guaranteed to work
   - Survives browser cache clears
   - Works in incognito mode
   - No dependencies needed

### Data Flow

**When you add a card:**
1. Saves to session state (in-memory)
2. Tries to save to localStorage (if available)
3. **Always** saves to file: `~/.churnpilot/cards.json`

**When app starts:**
1. Tries to load from localStorage first
2. Falls back to file if localStorage fails/empty
3. Starts fresh if no data found

**Result:** Your data is **always** backed up to a file!

---

## Troubleshooting

### Problem: Cards disappear after restarting

**Check:**
1. Does the file exist?
   ```bash
   ls ~\.churnpilot\cards.json
   ```

2. Does it contain your cards?
   ```bash
   cat ~\.churnpilot\cards.json
   ```

3. Check terminal output when starting app:
   ```
   [DEBUG] Initialized empty cards_data
   [DEBUG] Loading data...
   [DEBUG] Loaded X cards from file
   ```

**If file doesn't exist:**
- Check file permissions on `~/.churnpilot/` directory
- Run `test_hybrid_storage.py` to verify file creation works

**If file exists but cards don't load:**
- Check terminal for error messages
- Verify JSON is valid: `python -m json.tool ~/.churnpilot/cards.json`

### Problem: localStorage warnings

**Symptoms:**
```
To use Custom Components in Streamlit, you need to install PyArrow
```

**Solution:**
```bash
pip install pyarrow
```

**Note:** This is optional - file storage works without PyArrow. localStorage just won't work, but file backup will.

### Problem: Tab keeps switching to Dashboard

**Cause:** Some operations still call `st.rerun()` which resets tabs

**Affected operations:**
- Editing cards
- Deleting cards
- Marking benefits as used
- Most buttons that update data

**This is a Streamlit limitation** - tabs can't be programmatically selected. The data is still saved correctly even though the tab switches.

---

## Dependencies

### Required
- `streamlit>=1.39.0`
- `anthropic>=0.39.0`
- `pydantic>=2.0.0`
- `pandas>=2.0.0`

### Optional (for localStorage)
- `streamlit-js-eval>=0.1.7` ✓ Installed
- `pyarrow` ← Install if you want localStorage

### Install all:
```bash
pip install -r requirements.txt
pip install pyarrow  # Optional
```

---

## For Pilot Users

### What They Need to Know

**Data Storage:**
- Each user has their own data file: `~/.churnpilot/cards.json`
- Data does NOT sync across devices
- Each device has its own separate data
- Data survives app redeployments ✓

**Data Backup:**
- Export data regularly: Dashboard → Export button
- Save the JSON file somewhere safe
- Import on other devices if needed

**Privacy:**
- Data never leaves their computer
- Stored locally in their home directory
- Not shared with other users
- Not sent to any server (except AI for parsing)

### Multi-Device Setup

**Option 1: Manual Export/Import**
1. Device A: Export to JSON
2. Transfer file to Device B (email, USB, cloud)
3. Device B: Import JSON

**Option 2: Shared File**
- Put `~/.churnpilot/` in Dropbox/OneDrive
- Symlink from both devices
- Data syncs automatically via cloud

---

## Testing Checklist for Deployment

Before deploying to pilot users, verify:

- [ ] Add card from library works
- [ ] Card appears in Dashboard after switching tabs
- [ ] Close browser → Reopen → Card still there
- [ ] File exists at `~/.churnpilot/cards.json`
- [ ] Run `test_hybrid_storage.py` → All tests pass
- [ ] Import CSV works (27 cards test)
- [ ] Edit card works
- [ ] Delete card works
- [ ] Export data works
- [ ] Import data works
- [ ] Data persists after Streamlit restart
- [ ] Data persists in incognito mode

---

## Known Limitations

1. **Tabs reset after operations** - Streamlit limitation, can't fix
2. **No multi-device sync** - By design (local-first approach)
3. **localStorage may not work** - That's why we have file fallback
4. **Browser-specific data** - Different browsers = different data

---

## Future Improvements (Not Implemented)

### For Better Testing
- Selenium end-to-end tests (automated browser testing)
- Pytest integration tests for all UI flows
- Continuous testing on commit

### For Better UX
- Query params to maintain tab state across reruns
- Sidebar navigation instead of tabs
- Real-time auto-save indicator
- Data sync across devices (requires backend)

---

## Contact

If you find bugs or issues:
1. Check this guide first
2. Check `~/.churnpilot/cards.json` exists and has data
3. Check terminal output for [DEBUG] messages
4. Share the error message and steps to reproduce

**Debug checklist:**
- Terminal output (`[DEBUG]` lines)
- Browser console (F12 → Console)
- File contents (`~/.churnpilot/cards.json`)
- Steps to reproduce the issue
