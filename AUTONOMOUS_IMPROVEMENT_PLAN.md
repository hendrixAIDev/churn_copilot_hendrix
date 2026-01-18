# Autonomous Improvement Plan - Overnight Iteration

## Context
User is sleeping. Full permission granted for workspace commands. Goal: Improve ChurnPilot without requiring user guidance.

## Guiding Principles
1. **Polish over features** - Focus on making existing experience better
2. **No breaking changes** - User is about to deploy, stability is critical
3. **Test everything** - Run checks after each change
4. **Document decisions** - User reviews in the morning

---

## Priority 1: Card Library Feature (HIGH VALUE) ✅ PLANNED

**Status:** Detailed plan already exists from previous session

**What it does:** Users can select pre-defined card templates (e.g., "Amex Platinum") instead of manually entering all card details. Saves time and reduces errors.

**Why autonomous:**
- Complete specification already documented
- No user input needed for implementation
- Clear test criteria
- High impact for user experience

**Plan location:** `C:\Users\JayCh\.claude\plans\greedy-forging-boole.md`

**Implementation checklist:**
- [ ] Create `src/core/library.py` with CardTemplate model and CARD_LIBRARY
- [ ] Add Amex Platinum template with all credits
- [ ] Add `nickname` field to Card model
- [ ] Update `src/core/__init__.py` exports
- [ ] Add "Add from Library" tab in UI
- [ ] Test: Select template, save card, verify all fields populated
- [ ] Commit with descriptive message

**Estimated impact:** 🔥🔥🔥 (Major UX improvement for beginners)

---

## Priority 2: Fix Remaining Pre-Deployment Issues (MEDIUM VALUE)

**Status:** Automated checker found 18 issues, only critical styling fixed

**What's left:**
- 13 usability issues (complex inputs without help text)
- Some may be false positives (need to review)

**Why autonomous:**
- Mostly adding help text to inputs
- Clear guidelines for what makes good help text
- Can test by running app

**Implementation:**
- [ ] Review each flagged input
- [ ] Add concise, beginner-friendly help text
- [ ] Re-run checker to verify all issues resolved
- [ ] Commit

**Estimated impact:** 🔥 (Nice polish, but not blocking)

---

## Priority 3: Input Validation & Error Messages (MEDIUM VALUE)

**What:** Add validation to prevent common user errors

**Examples:**
- Opened date in future → Show warning
- Annual fee negative → Show error
- Signup bonus spend requirement = 0 → Show warning
- Duplicate card names → Show warning

**Why autonomous:**
- Clear what constitutes invalid input
- Can implement without design decisions
- Improves reliability before beta testing

**Implementation:**
- [ ] Add validation functions to `src/core/models.py`
- [ ] Add error/warning display in UI
- [ ] Test with edge cases
- [ ] Commit

**Estimated impact:** 🔥🔥 (Prevents user confusion)

---

## Priority 4: Update CLAUDE.md with Permissions (LOW VALUE)

**What:** Document that full workspace permissions are granted

**Why autonomous:**
- User explicitly requested this
- Simple documentation change
- No testing needed

**Implementation:**
- [ ] Add "Permissions" section to CLAUDE.md
- [ ] Document scope: full workspace access for this project
- [ ] Commit

**Estimated impact:** 🔥 (Housekeeping)

---

## Priority 5: Loading States & Progress Indicators (LOW VALUE)

**What:** Add spinners/progress bars for long operations (spreadsheet import, URL extraction)

**Why NOT fully autonomous:**
- Requires UX decisions (where to place, what text to show)
- Might conflict with user's vision
- Lower priority than functionality

**Decision:** SKIP for now, suggest to user in morning review

---

## Priority 6: Additional Card Templates (LOW VALUE)

**What:** Add more card templates beyond Amex Platinum (Chase Sapphire Reserve, Amex Gold, etc.)

**Why NOT fully autonomous:**
- Need to research accurate credit amounts for each card
- User might have specific cards they want prioritized
- Can add more after user validates the feature works

**Decision:** Only implement Amex Platinum initially, document how to add more

---

## Execution Order

1. ✅ **Card Library Feature** - Biggest value, clear spec
2. ✅ **Input Validation** - Prevents bugs before beta testing
3. ✅ **Pre-deployment Issues** - Polish for launch
4. ✅ **Update CLAUDE.md** - Quick documentation
5. ❌ **Loading States** - Skip, too subjective
6. ❌ **More Templates** - Skip, start with one

---

## Testing Strategy

After each change:
1. **Syntax check:** `python -m py_compile [file]`
2. **Import check:** `python -c "import module"`
3. **Run app:** `streamlit run src/ui/app.py` (verify in browser)
4. **Pre-deployment check:** `python scripts/pre_deployment_check.py`

---

## Git Strategy

- Commit after each feature/fix (not one giant commit)
- Descriptive messages: `feat: add card library with Amex Platinum template`
- Create summary commit at end: `chore: autonomous improvements for deployment`

---

## Morning Review Document

Will create `OVERNIGHT_CHANGES.md` summarizing:
- What was implemented
- What was skipped and why
- Any decisions made
- How to test changes
- Suggestions for next steps

---

## Risk Mitigation

**What if something breaks?**
- All changes are in Git - user can revert
- Each commit is atomic - can cherry-pick good changes
- No changes to deployment config (already working)

**What if I make wrong UX decision?**
- Focus on backend logic (library system) not visual design
- Use existing UI patterns consistently
- Document any subjective choices for user review

---

## Success Criteria

**Minimum success:**
- Card library feature working end-to-end
- No new bugs introduced
- All tests pass

**Stretch success:**
- All pre-deployment issues resolved
- Input validation prevents common errors
- User wakes up to significantly improved app ready for beta testing

---

**Let's begin with Priority 1: Card Library Feature**
