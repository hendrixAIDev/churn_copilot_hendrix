# ChurnPilot Test Health Report
**Date:** 2026-02-01

## Summary
| Category | Count | Status |
|----------|-------|--------|
| Unit tests (fast, no DB) | ~142 | ✅ All pass (<2s total) |
| DB-dependent tests | ~14+ | ⚠️ Hang without DB connection |
| Browser/E2E tests | ~7 files | ⚠️ Require Selenium + running server |
| Total test files | 36 | Mixed |

## Fast Unit Tests (ALL PASS)
These run in <2s with no external dependencies:

| File | Tests | Result |
|------|-------|--------|
| test_auth.py | 7 | ✅ Pass |
| test_five_twenty_four.py | 8 | ✅ Pass |
| test_normalize.py | 22 | ✅ Pass |
| test_periods.py | 29 | ✅ Pass |
| test_library.py | 22 | ✅ Pass |
| test_preferences.py | 6 | ✅ Pass |
| test_user_model.py | 3 | ✅ Pass |
| test_importer.py | 10 pass, 5 skip | ✅ Pass (skips need Anthropic API) |
| test_web_storage.py | 30 | ✅ Pass |
| test_retention_offers.py | 4 | ✅ Pass |
| test_edge_cases.py | TBD | ✅ Pass |
| **Total** | **~142** | **✅** |

## Known Issues

### test_amex_platinum.py — 1 FAILURE
- 1 failed, 1 skipped
- Needs investigation (likely data fixture issue)

### test_card_add_refresh.py — HANGS
- 14 tests, all import `DatabaseStorage` + `AuthService`
- Hangs trying to connect to Supabase DB
- **Fix:** Mock the DB connection or mark as integration tests

### DB-Dependent Tests (HANG without connection)
These files import `DatabaseStorage` or `AuthService` with real DB:
- test_card_add_refresh.py
- test_connection_stability.py
- test_data_integrity.py
- test_database.py
- test_db_storage.py
- test_integration.py
- test_performance.py
- test_persistence_stress.py
- test_schema_health.py
- test_security.py
- test_session_persistence.py
- test_setup.py
- test_storage_library.py

**Impact:** Full `pytest tests/` hangs indefinitely. Sub-agents time out.

### Browser/E2E Tests (Require Selenium)
- test_e2e_auth.py
- test_e2e_automated.py
- test_e2e_cards.py
- test_e2e_with_logs.py
- test_browser_persistence.py
- test_bug_scenarios_browser.py
- test_user_journeys_browser.py

## Recommendations

### 1. Fix Makefile test target (HIGH PRIORITY)
Update `test-churnpilot` in Makefile to only run fast unit tests:
```
venv/bin/python -m pytest tests/test_auth.py tests/test_five_twenty_four.py tests/test_normalize.py tests/test_periods.py tests/test_library.py tests/test_preferences.py tests/test_user_model.py tests/test_importer.py tests/test_web_storage.py tests/test_retention_offers.py tests/test_edge_cases.py --timeout=10 -q
```

### 2. Add pytest markers
Mark tests by category so we can run `pytest -m unit` vs `pytest -m integration`:
- `@pytest.mark.unit` — fast, no external deps
- `@pytest.mark.db` — needs database connection
- `@pytest.mark.browser` — needs Selenium + running server

### 3. Fix test_amex_platinum.py failure

### 4. Mock DB in integration tests
Add a SQLite-based mock or use `pytest-mock` to stub `DatabaseStorage` so these tests don't hang.
