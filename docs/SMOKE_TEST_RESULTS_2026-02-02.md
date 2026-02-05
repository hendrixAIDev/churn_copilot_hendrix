# ChurnPilot Smoke Test Results
**Date:** 2026-02-02  
**Tester:** Hendrix (Sub-agent)  
**Environment:** Local (localhost:8501)  
**Browser:** Chrome (openclaw profile)

---

## Test Results Summary
**Status:** ❌ CRITICAL BUG FOUND  
**Tests Passed:** 4/5  
**Tests Failed:** 1/5 (Critical)

---

## Detailed Test Results

### ✅ Test 1: User Registration
**Status:** PASSED  
**Steps:**
1. Navigated to localhost:8501
2. Clicked "Create Account" tab
3. Filled in:
   - Email: smoketest20260202@test.com
   - Password: TestPass123!
   - Confirm Password: TestPass123!
4. Clicked "Create Account" button

**Result:** Registration successful, automatically logged in, dashboard displayed

---

### ✅ Test 2: Add Card to Dashboard
**Status:** PASSED  
**Steps:**
1. Clicked "Add Card" tab
2. Selected Issuer: Chase
3. Selected Card: Chase Sapphire Preferred Credit Card
4. Entered Opened Date: 2026/02/02
5. Clicked "Add Card" button

**Result:** 
- Success message displayed: "✓ Successfully added: Chase Sapphire Preferred Credit Card"
- Sidebar updated with portfolio stats:
  - Quick Stats: Chase: 1
  - Annual Fees: $95
  - Benefits Value: $290
  - Net Value: $195 (Positive ROI)
  - Chase 5/24 Status: 1/5 - Can apply
  - Next drop: 2028-03-01 (758d)

---

### ✅ Test 3: Page Refresh - Session Persistence
**Status:** PASSED  
**Steps:**
1. Pressed F5 to refresh page
2. Waited for page reload

**Result:** 
- User still logged in as smoketest20260202@test.com
- All dashboard data intact
- Card information preserved
- No redirect to login page

---

### ❌ Test 4: New Tab Direct Navigation - Session Persistence
**Status:** FAILED - CRITICAL BUG  
**Steps:**
1. Opened new browser tab
2. Typed localhost:8501 in address bar
3. Navigated to URL

**Result:** 
- Session NOT preserved
- User redirected to login/registration page
- No authentication state carried over to new tab

**Expected:** User should remain logged in across tabs  
**Actual:** Session lost, shows login page

**Impact:** CRITICAL - This is the primary bug the session persistence fix was meant to address. Users will be logged out whenever they:
- Open the app in a new tab
- Navigate directly via URL (not refresh)
- Close and reopen the tab

**Technical Notes:**
- Same-tab refresh works (Test 3 passed)
- New tab/direct navigation fails (Test 4 failed)
- Suggests `streamlit_js_eval` + `window.parent.localStorage` is writing the token but not reading it back on initial page load in new contexts
- Possible timing issue: component mounting returns None on first render, but app may not be handling the second render correctly
- May need to investigate component initialization sequence

---

### ✅ Test 5: Logout - Session Cleanup
**Status:** PASSED  
**Steps:**
1. Clicked "Sign Out" button in sidebar
2. Waited for logout to complete

**Result:**
- Successfully logged out
- Redirected to Sign In page
- Session cleared
- No user data visible

---

## UX Observations

### Positive
1. **Clean Registration Flow:** Simple, intuitive form with clear validation
2. **Card Addition UX:** Library-based selection is fast and efficient
3. **Portfolio Stats:** Sidebar provides excellent at-a-glance information
4. **Success Feedback:** Clear confirmation messages on card addition
5. **Value Visualization:** Net value calculation (+$195) is compelling
6. **5/24 Tracker:** Chase rule tracking is prominent and useful

### Issues
1. **CRITICAL: Session Persistence Broken for New Tabs** (See Test 4)
2. **Dependencies Not Installed:** Had to recreate venv and install python-dotenv before testing could begin
3. **No Loading States:** Card addition happens instantly with no progress indicator (minor, acceptable for local)

---

## Blockers & Recommendations

### Immediate Priority
**P0 - Session Persistence Fix:**
The new tab navigation bug is a critical UX failure. Recommendations:
1. Debug `streamlit_js_eval` component initialization sequence
2. Add debug logging to see when localStorage is being read vs. written
3. Consider fallback to `st.query_params` for new tab cases (though this has limitations)
4. Test two-phase rendering: first render returns None, second render should return token value
5. Verify `window.parent.localStorage` is accessible from Streamlit's iframe context in all scenarios

### Secondary Issues
**P1 - Deployment Reliability:**
- Document/automate venv setup process
- Add dependency check at app startup with clear error messages
- Consider requirements.txt validation in CI/CD

---

## Environment Details
- **Python:** 3.14
- **Streamlit:** 1.53.1
- **Database:** PostgreSQL (local)
- **Session Management:** streamlit_js_eval + window.parent.localStorage
- **Browser:** Chrome 132.x

---

## Next Steps
1. Fix critical session persistence bug for new tab navigation
2. Re-run smoke tests after fix
3. Add automated browser tests for session persistence scenarios
4. Consider E2E test coverage for:
   - Multiple tabs
   - Browser restart
   - Session expiration
   - Token refresh

---

**Test Conclusion:** ChurnPilot core functionality works well, but the critical session management bug must be fixed before this can be considered production-ready or handed off to JJ for preview.
