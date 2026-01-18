# ChurnPilot - Development Guidelines

## Project Overview

ChurnPilot is an AI-powered credit card churning management system. The architecture prioritizes **modularity** to allow UI framework swaps (Streamlit → React) without touching core business logic.

## Permissions

**Full workspace permissions granted for this project:**

Claude has been granted full autonomy within this workspace to:
- Create, modify, and delete files
- Run git commands (add, commit, push, etc.)
- Execute tests and verification scripts
- Install dependencies via pip
- Run deployment checks
- Make architectural decisions for improvements
- Commit changes with co-authorship attribution

**Scope:** All permissions are limited to this workspace (`C:\Users\JayCh\workspace\churn_copilot\`)

**Safety guardrails:**
- No destructive git operations without explicit approval (force push, hard reset)
- No modifications to production deployment secrets
- All changes committed to git for easy rollback
- Major architectural changes should be documented in plan mode first

**Autonomous improvement guidelines:**
- Focus on high-impact user experience improvements
- Maintain code quality and testing standards
- Document all decisions for user review
- Prefer polish over new features when working without user guidance

## Architecture Principles

### Separation of Concerns

```
src/
├── core/           # Framework-agnostic business logic
│   ├── extractor.py    # AI extraction (Anthropic API)
│   ├── models.py       # Pydantic data models
│   └── storage.py      # Data persistence layer
└── ui/             # UI layer (currently Streamlit)
    └── app.py
```

- **core/** must have ZERO UI dependencies
- **ui/** imports from core, never the reverse
- All AI logic lives in `core/extractor.py`

## Coding Standards

### Type Hints (Required)

All functions must have complete type annotations:

```python
def extract_card_data(raw_text: str) -> CardData:
    ...

def get_cards_by_issuer(issuer: str) -> list[Card]:
    ...
```

### Docstrings (Google Style)

```python
def parse_annual_fee(text: str) -> int | None:
    """Extract annual fee amount from card terms text.

    Args:
        text: Raw text containing card terms and conditions.

    Returns:
        Annual fee in dollars, or None if not found.

    Raises:
        ExtractionError: If text format is invalid.
    """
```

### Pydantic Models for Data

All structured data uses Pydantic for validation:

```python
from pydantic import BaseModel
from datetime import date

class Card(BaseModel):
    name: str
    issuer: str
    annual_fee: int
    signup_bonus: SignupBonus | None
    credits: list[Credit]
```

### Error Handling

- Use custom exceptions in `core/exceptions.py`
- Never let raw API errors bubble to UI
- Log errors with context

### Naming Conventions

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## AI Integration Guidelines

### Anthropic API Usage

- Model: `claude-sonnet-4-20250514` for extraction tasks
- Always use structured output (JSON mode) for parsing
- Keep prompts in separate constants for maintainability
- Include retry logic with exponential backoff

### Prompt Engineering

- Extraction prompts live in `core/prompts.py`
- Version prompts with comments
- Test prompts against edge cases before deploying

## Testing

- Unit tests in `tests/` mirror `src/` structure
- Mock external APIs in tests
- Minimum coverage: core extraction logic

## Environment

- Python 3.11+
- Dependencies in `requirements.txt`
- Secrets via environment variables (never commit)

## Change Verification

**Always verify changes compile/run before completing a task:**

```bash
# 1. Syntax check (catches typos, missing colons, etc.)
python -m py_compile src/core/module.py

# 2. Import check (catches missing dependencies, import errors)
# IMPORTANT: py_compile does NOT catch import errors!
python -c "import src.core.module"

# 3. Run the app to verify full functionality
streamlit run src/ui/app.py
```

**Verification Levels:**
| Check | Catches | Misses |
|-------|---------|--------|
| `py_compile` | Syntax errors | Missing imports, bad imports |
| `import module` | Import errors, missing deps | Runtime errors |
| Run app | Most issues | Edge cases |

**When adding new dependencies:**
1. Add to `requirements.txt`
2. **Always remind user to run `pip install -r requirements.txt`** - never assume they will do this
3. Verify with import check, not just syntax check

**Rules:**
- Never assume code works - verify it
- `py_compile` is NOT sufficient for files with new imports
- **Always use import checks (`python -c "import module"`) not just syntax checks for files with new imports**
- Test new features manually after implementation

## Git Workflow

- Commit messages: `type: description` (e.g., `feat: add SUB deadline parsing`)
- Types: `feat`, `fix`, `refactor`, `docs`, `test`

---

## Development Workflows

### Feature Development Workflow

**Standard flow for implementing new features:**

1. **Requirements Gathering**
   - Clarify user needs and expected behavior
   - Identify deployment context (web/desktop, mobile users)
   - Document in plan mode for complex features

2. **Implementation**
   - Start with core logic (framework-agnostic)
   - Add UI layer last
   - Commit incrementally with descriptive messages

3. **Verification** (see detailed sections below)
   - Syntax/import checks
   - **User-facing testing** (critical - see below)
   - Deployment context validation

4. **Documentation**
   - Update docstrings
   - Add to execution logs if significant
   - Update README if user-facing

### User-Facing Testing Workflow

**CRITICAL: Always test like a real user, not just verify code compiles.**

This workflow prevents bugs that only appear in real usage:

```bash
# 1. Start the application
streamlit run src/ui/app.py

# 2. Open in browser (Streamlit auto-opens, or navigate to http://localhost:8501)

# 3. Test critical user journeys:
```

**Critical User Journeys to Test:**

1. **Adding Cards**
   - ✓ Add card from URL (paste URL, click extract)
   - ✓ Add card from library (select template, enter details)
   - ✓ Verify card appears in dashboard
   - ✓ Check tab doesn't unexpectedly switch

2. **Viewing Cards**
   - ✓ Dashboard loads with all cards
   - ✓ Cards display correct information
   - ✓ Filtering works (by issuer, search)
   - ✓ Sorting works (by date, fee, etc.)

3. **Editing Cards**
   - ✓ Click edit on a card
   - ✓ Modify fields
   - ✓ Save changes
   - ✓ Verify updates appear

4. **Benefits Tracking**
   - ✓ Mark credit as used this period
   - ✓ Verify checkmark appears
   - ✓ Snooze reminders
   - ✓ Check Action Required tab updates

5. **Data Persistence** (CRITICAL)
   - ✓ Add/modify data
   - ✓ **Close browser completely**
   - ✓ **Reopen browser and navigate to app**
   - ✓ **Verify data is still there**

6. **Import/Export**
   - ✓ Export data (download JSON)
   - ✓ Clear all data
   - ✓ Import from JSON
   - ✓ Verify all cards restored correctly

7. **Edge Cases**
   - ✓ Test with empty state (no cards)
   - ✓ Test with many cards (20+)
   - ✓ Test with missing optional fields
   - ✓ Test invalid inputs

**Why This Matters:**

Example bugs caught ONLY by user-facing testing:
- `st.rerun()` causing tab switches (syntax check passed ✓, but UX broken ✗)
- Data not persisting after browser restart (code compiled ✓, but storage broken ✗)
- File storage on server won't work for mobile users (logic correct ✓, deployment context wrong ✗)

### Bug Fix Workflow

**When user reports a bug:**

1. **Reproduce**
   - Follow exact steps user described
   - Verify bug exists in current code
   - Document reproduction steps

2. **Diagnose Root Cause**
   - Read relevant code sections
   - Check execution logs
   - Consider deployment context
   - Don't assume - investigate

3. **Fix with Minimal Changes**
   - Target the root cause
   - Avoid scope creep
   - Don't refactor unrelated code
   - Keep changes focused

4. **Test the Fix**
   - Verify bug no longer reproduces
   - **User-facing testing** (see above)
   - Check for regressions

5. **Document**
   - Clear commit message explaining what was wrong
   - Update execution logs if significant
   - Add comment if fix is non-obvious

### Iterative Improvement Workflow

**Continuous improvement based on feedback:**

1. **Gather Feedback**
   - User pain points
   - Credit card forum discussions
   - Your own observations during testing

2. **Prioritize**
   - Critical bugs first
   - High-impact UX improvements
   - Nice-to-haves last

3. **Small Iterations**
   - One improvement at a time
   - Test after each change
   - Commit incrementally

4. **Validate**
   - Get user confirmation
   - Test with real workflows
   - Measure impact

5. **Repeat**
   - Build on learnings
   - Refine approach
   - Keep improving

---

## Deployment Context Considerations

**Critical: Storage approach depends on deployment context**

### Web Deployment (Streamlit Cloud, Heroku, etc.)

**Context:**
- Multiple users accessing same app instance
- Server filesystem is ephemeral (resets on redeployment)
- Mobile users can't access server file paths
- Each user needs isolated data

**Storage Requirements:**
- ✓ Browser localStorage (client-side)
- ✗ Server file storage (ephemeral, shared)
- ✗ File paths like `~/.churnpilot/cards.json` (server-side only)

**Implementation:**
- Use `WebStorage` class (browser localStorage only)
- Data stored in user's browser
- Survives redeployments
- Works on mobile, desktop, tablet
- Each user has private data

**Key Files:**
- `src/core/web_storage.py` - Browser-only storage
- Uses `streamlit-js-eval` for localStorage access
- Requires `pyarrow` dependency

### Desktop Deployment (localhost, single user)

**Context:**
- One user running locally
- Persistent file system
- Can use file-based storage

**Storage Options:**
- ✓ File storage (e.g., `~/.churnpilot/cards.json`)
- ✓ SQLite database
- ✓ Can also use localStorage for web-like experience

**Implementation:**
- Use `CardStorage` class (file-based)
- Data persists across restarts
- Easy to backup/migrate
- Can edit manually

### Common Mistakes

**❌ Wrong: Using file storage for web deployment**
```python
# This won't work for mobile users or survive redeployments:
STORAGE_PATH = Path.home() / '.churnpilot' / 'cards.json'
```

**✓ Right: Use browser localStorage for web deployment**
```python
# Data stored in user's browser, works everywhere:
localStorage.setItem('churnpilot_cards', JSON.stringify(data))
```

**❌ Wrong: Assuming server paths work for all users**
```python
# Mobile users can't access server filesystem:
with open('~/.churnpilot/cards.json', 'r') as f:
    data = json.load(f)
```

**✓ Right: Consider deployment context**
```python
# Check if we're in web or desktop context:
if is_web_deployment():
    storage = WebStorage()  # Browser localStorage
else:
    storage = CardStorage()  # File-based
```

---

## Streamlit-Specific Gotchas

**Important considerations when using Streamlit:**

### 1. Tab Rendering Order (CRITICAL)

**Problem:**
- Streamlit renders ALL tab content in order on every rerun
- Dashboard (tab 1) renders BEFORE Add Card (tab 3) processes button clicks
- If button handler adds data, Dashboard already rendered with OLD data

**Example of the Bug:**
```python
# main() execution order on button click:
1. render_dashboard()      # Reads cards - sees OLD data (card not added yet)
2. render_add_card_tab()   # Button handler runs, adds card to session_state
3. Script ends            # Dashboard already rendered with stale data!
```

**Result:** User adds card, switches to Dashboard, card not there!

**Solution:** MUST use `st.rerun()` after modifying data
```python
# ✓ Correct: Use st.rerun() after data modification
card = storage.add_card_from_template(...)
st.session_state.card_just_added = card.name  # Store for success message
st.rerun()  # Forces fresh render with updated data

# In render_dashboard():
if st.session_state.get("card_just_added"):
    st.success(f"✓ Added: {st.session_state.card_just_added}")
    st.session_state.card_just_added = None
```

**Why This Works:**
- `st.rerun()` causes fresh execution
- On new run, session_state has updated data
- Dashboard renders with correct data
- Success message shows via session_state flag

**Previous Wrong Approach:**
```python
# ❌ Bad: No rerun - card won't appear until NEXT interaction
st.success("Card added!")
st.info("Switch to Dashboard tab to see your card")
# Data in session_state but Dashboard already rendered!
```

### 2. Session State vs Persistent Storage

**Streamlit session state:**
- In-memory only
- Lost on browser refresh
- Separate per tab/window
- Fast access

**Persistent storage (localStorage/files):**
- Survives browser restarts
- Shared across tabs (localStorage)
- Slower access
- Requires serialization

**Best Practice:**
```python
# Use session state as cache
if "cards_data" not in st.session_state:
    # Load from persistent storage once
    st.session_state.cards_data = load_from_storage()

# Work with session state
cards = st.session_state.cards_data

# Save to persistent storage when changed
save_to_storage(cards)
```

### 3. JavaScript Evaluation Timing

**Issue:** `streamlit-js-eval` can return None due to timing issues

**Root Cause:**
- JavaScript runs asynchronously in browser
- Streamlit Python continues execution
- Result may not be ready when Python checks

**Solution:** Use simple synchronous JavaScript (NOT Promises)
```python
# ❌ Bad: Promises don't work reliably with streamlit_js_eval
js_code = """
new Promise((resolve) => {
    resolve(localStorage.getItem('key'));
})
"""

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
result = streamlit_js_eval(js=js_code, key="unique_static_key")
```

**For Saves:** Use `streamlit_js_eval` (more reliable than HTML injection)
```python
# ✓ Good: streamlit_js_eval for saves
js_code = f"""
(function() {{
    localStorage.setItem('key', JSON.stringify({data}));
    return true;
}})()
"""
streamlit_js_eval(js=js_code, key=f"save_{time.time()}")
```

**Retry Logic for Loads:**
```python
# Handle None returns with retry
if not st.session_state.storage_initialized:
    if result is None:
        st.session_state.storage_load_attempts += 1
        if attempt >= 3:
            st.session_state.storage_initialized = True  # Give up
    else:
        st.session_state.cards_data = result
        st.session_state.storage_initialized = True
```

**Requirements:**
- Requires `pyarrow` to be installed
- Use SIMPLE synchronous JavaScript (no Promises)
- Always update session_state FIRST before localStorage
- Handle None/null returns with retry logic

### 4. Widget State Persistence

**Problem:** Widget values don't persist across reruns unless using `key` parameter

```python
# ❌ Bad: Value lost on rerun
card_name = st.text_input("Card Name")

# ✓ Good: Value persists in session state
card_name = st.text_input("Card Name", key="card_name_input")
# Access later: st.session_state.card_name_input
```

---

## Testing Strategy

### Levels of Testing

| Level | What It Tests | When to Use |
|-------|---------------|-------------|
| **Unit Tests** | Individual functions, pure logic | Core business logic, utilities |
| **Integration Tests** | Module interactions | Storage + models, extractor + API |
| **Syntax Checks** | Code compiles | After every change |
| **Import Checks** | Dependencies available | After adding imports/deps |
| **User-Facing Tests** | Real user workflows | **Always before saying "done"** |

### Pre-Commit Checklist

Before committing any feature or fix:

- [ ] **Syntax check passes:** `python -m py_compile <files>`
- [ ] **Import check passes:** `python -c "import module"`
- [ ] **App starts:** `streamlit run src/ui/app.py`
- [ ] **Critical user journeys work** (add card, view, edit, persist)
- [ ] **No console errors** (check browser console, terminal output)
- [ ] **Deployment context considered** (web vs desktop)
- [ ] **Commit message is descriptive**

### Pre-Deployment Checklist

Before sharing with pilot users:

- [ ] **All pre-commit checks pass**
- [ ] **Test data persistence** (close browser, reopen, verify)
- [ ] **Test on target platform** (Streamlit Cloud, not just localhost)
- [ ] **Test on mobile device** (if web deployment)
- [ ] **Test in incognito mode** (privacy settings)
- [ ] **Export/import works**
- [ ] **Dependencies documented** (`requirements.txt` up to date)
- [ ] **User-facing documentation updated** (if needed)

---

## Common Pitfalls and Solutions

### Pitfall 1: Only Testing Code Compilation

**Symptom:** Code compiles and imports work, but app breaks in real usage

**Example:**
```python
# This compiles fine:
st.success("Card added")
st.rerun()

# But causes tab switching bug in real usage
```

**Solution:** Always do user-facing testing (see workflow above)

### Pitfall 2: Wrong Deployment Context

**Symptom:** Works on localhost, breaks in production

**Example:**
- File storage at `~/.churnpilot/cards.json` works locally
- Breaks on Streamlit Cloud (ephemeral filesystem)
- Mobile users can't access it

**Solution:** Design for target deployment from the start

### Pitfall 3: Assuming Browser APIs Just Work

**Symptom:** localStorage code looks correct but data doesn't persist

**Potential Causes:**
- Missing `pyarrow` dependency
- Browser privacy settings blocking localStorage
- JavaScript timing issues with `streamlit-js-eval`
- Incognito mode restrictions
- Insufficient localStorage quota

**Solution:**
- Create diagnostic tools (like `diagnose_storage.py`)
- Test in multiple browsers
- Check browser console for errors
- Handle failures gracefully

### Pitfall 4: Over-Engineering Solutions

**Symptom:** Complex implementation when simple solution exists

**Example:**
- Created HybridStorage (localStorage + file fallback)
- File fallback doesn't help web users
- Simple WebStorage (localStorage only) was sufficient

**Solution:**
- Start with simplest approach that meets requirements
- Add complexity only when proven necessary
- Question assumptions (ask "why do we need this?")

---

## Lessons Learned

### Key Insights from Development

1. **User-facing testing is not optional**
   - Compilation ≠ working software
   - Always test like a real user
   - Close and reopen to test persistence

2. **Deployment context matters immensely**
   - What works locally may not work in production
   - Mobile users have different constraints
   - Server storage ≠ client storage

3. **Simple is better**
   - Don't add "just in case" features
   - Solve the actual problem, not hypothetical ones
   - Easier to add complexity than remove it

4. **Framework quirks require deep understanding**
   - Streamlit tab rendering order affects data visibility
   - `st.rerun()` is REQUIRED after data changes (not optional!)
   - Session state updates are synchronous, but tab content already rendered
   - JavaScript eval timing requires retry logic

5. **Real user feedback is invaluable**
   - Users catch what developers miss
   - Test with real workflows
   - Listen to pain points

6. **Understand root cause before fixing (January 2026)**
   - Bug: "Card not appearing after add" - seemed like localStorage issue
   - Root cause: Tab rendering order - Dashboard rendered BEFORE add handler ran
   - Wrong fix: Avoid st.rerun() - made it worse!
   - Right fix: USE st.rerun() + session state for success message
   - Lesson: Trace execution order, don't assume

7. **Test persistence end-to-end**
   - Add card → appears immediately (session state)
   - Close browser → reopen → card still there (localStorage)
   - Both must work!

---

## Staff Engineer Mode

**When user says "work on this for X hours" or "be a staff engineer":**

This means the user wants autonomous, thorough work. Act as a senior engineer who:

1. **Takes ownership of the problem**
   - Don't ask for permission on small decisions
   - Make architectural choices and document them
   - Iterate until the problem is truly solved

2. **Does deep investigation before fixing**
   - Read the full architecture, not just the bug location
   - Trace execution paths completely
   - Understand WHY the bug exists, not just WHERE

3. **Writes comprehensive tests**
   - Tests should cover the exact bug scenario
   - Include edge cases discovered during investigation
   - Tests prevent regression

4. **Documents lessons learned**
   - Update CLAUDE.md with insights
   - Future sessions benefit from documented knowledge
   - Explain root cause, not just the fix

5. **Commits incrementally with clear messages**
   - Each commit should be atomic and reviewable
   - Commit message explains what and why

**Example Staff Engineer Workflow:**
```
1. User: "Fix this bug, work autonomously"
2. Read full codebase architecture (not just bug file)
3. Trace execution to understand data flow
4. Identify root cause (not symptoms)
5. Implement fix
6. Write tests for the specific failure
7. Update documentation with lessons
8. Commit with detailed message
9. Provide summary to user
```
