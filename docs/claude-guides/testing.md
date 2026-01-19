# Testing Strategy

## Levels of Testing

| Level | What It Tests | When to Use |
|-------|---------------|-------------|
| **Unit Tests** | Individual functions, pure logic | Core business logic, utilities |
| **Integration Tests** | Module interactions | Storage + models, extractor + API |
| **Syntax Checks** | Code compiles | After every change |
| **Import Checks** | Dependencies available | After adding imports/deps |
| **User-Facing Tests** | Real user workflows | **Always before saying "done"** |

## Change Verification

**Always verify changes compile/run before completing a task:**

```bash
# 1. Syntax check
python -m py_compile src/core/module.py

# 2. Import check (IMPORTANT: py_compile does NOT catch import errors!)
python -c "import src.core.module"

# 3. Run the app
streamlit run src/ui/app.py
```

## Pre-Commit Checklist

- [ ] Syntax check passes
- [ ] Import check passes
- [ ] App starts
- [ ] Critical user journeys work
- [ ] No console errors
- [ ] Commit message is descriptive

## Pre-Deployment Checklist

- [ ] All pre-commit checks pass
- [ ] Test data persistence (close browser, reopen, verify)
- [ ] Test on target platform (Streamlit Cloud, not just localhost)
- [ ] Test on mobile device (if web deployment)
- [ ] Export/import works
- [ ] Dependencies documented

## MANDATORY: Browser Verification for localStorage Features

**Unit tests are INSUFFICIENT for browser-dependent features.**

```bash
# 1. Start the app
streamlit run src/ui/app.py

# 2. Open browser developer tools (F12)
# 3. Go to Application tab > Local Storage > localhost:8501
```

| Test | Action | Expected |
|------|--------|----------|
| Add card | Add card from library | Card appears in Dashboard |
| Check localStorage | F12 > Application > Local Storage | `churnpilot_cards` key exists |
| Refresh test | F5 to refresh page | Card still there |
| Close/reopen | Close browser, reopen localhost:8501 | Card still there |

**If ANY test fails, the feature is NOT done.**

## Why Unit Tests Are Insufficient for Browser Features

Unit tests with mocked `streamlit_js_eval`:
- ✅ Verify Python logic is correct
- ❌ Do NOT verify JavaScript executes in browser
- ❌ Do NOT verify localStorage actually persists
- ❌ Do NOT verify data survives browser restart

**The only way to verify browser persistence is to test in an actual browser.**
