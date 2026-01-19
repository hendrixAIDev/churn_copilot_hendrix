# Current Bug: Data Persistence Issue

## Status: UNSOLVED

## Symptom
Cards disappear after browser refresh (user-reported, not reproduced by automated tests)

## What We Know
- `src/core/web_storage.py` handles localStorage
- Automated tests pass but don't catch real bug
- E2E Selenium test passes

## What We Don't Know
- Exact user steps to reproduce
- When exactly the card disappears (immediately? after delay?)
- Browser console errors (if any)

## Files Involved
- `src/core/web_storage.py` - Storage logic
- `src/ui/app.py` - Main UI (2300 lines)
- `tests/test_add_card_working.py` - E2E test

## Next Steps
1. User describes exact reproduction steps
2. Check browser console (F12) for errors
3. Check Application > Local Storage for data
4. Create minimal diagnostic script

## Recent Changes
- Refactored web_storage.py (simpler architecture)
- 5 retries instead of 8, 50ms delay instead of 100ms
- Immediate saves instead of deferred sync
