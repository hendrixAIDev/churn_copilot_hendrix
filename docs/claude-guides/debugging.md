# Debugging Guide

## Bug Fix Workflow

1. **Reproduce** - Follow exact steps user described
2. **Diagnose** - Read code, check logs, don't assume
3. **Fix** - Target root cause, minimal changes
4. **Test** - User-facing testing, check for regressions
5. **Document** - Clear commit message, update docs if needed

## Common Pitfalls

### Pitfall 1: Only Testing Code Compilation

**Symptom:** Code compiles but breaks in real usage

**Solution:** Always do user-facing testing

### Pitfall 2: Wrong Deployment Context

**Symptom:** Works on localhost, breaks in production

**Example:** File storage works locally but not on Streamlit Cloud

**Solution:** Design for target deployment from the start

### Pitfall 3: Assuming Browser APIs Just Work

**Symptom:** localStorage code looks correct but doesn't persist

**Potential Causes:**
- Missing `pyarrow` dependency
- Browser privacy settings
- JavaScript timing issues
- Incognito mode restrictions

**Solution:** Test in actual browser, check console for errors

### Pitfall 4: Over-Engineering

**Symptom:** Complex implementation when simple would work

**Solution:** Start simple, add complexity only when proven necessary

## Lessons Learned (January 2026)

1. **User-facing testing is not optional** - Compilation ≠ working software

2. **Deployment context matters** - Server storage ≠ client storage

3. **Simple is better** - Don't add "just in case" features

4. **Framework quirks require deep understanding** - Streamlit tab rendering order, st.rerun() timing

5. **Test persistence end-to-end:**
   - Add card → appears immediately (session state)
   - Close browser → reopen → card still there (localStorage)
   - Both must work!

6. **Understand root cause before fixing:**
   - Bug: "Card not appearing after add"
   - Wrong assumption: localStorage issue
   - Actual cause: Tab rendering order
   - Lesson: Trace execution order, don't assume
