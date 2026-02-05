# Security Hardening Complete - 2026-02-04

## Summary
Added rate limiting and input length limits to ChurnPilot to prevent abuse before public launch.

## Changes Implemented

### 1. Rate Limiting Module (`src/core/rate_limit.py`)
Created a new in-memory rate limiting system with the following features:

**Login Rate Limiting:**
- Max 5 failed attempts per email
- 15-minute lockout after reaching limit
- Counter resets on successful login
- User-friendly error messages showing remaining time

**Signup Rate Limiting:**
- Max 3 signup attempts per session per hour
- Uses Streamlit session ID (IP not available in Streamlit Cloud)
- Rolling 1-hour window

**Feedback Rate Limiting:**
- Max 5 feedback submissions per user per hour
- Rolling 1-hour window
- Prevents feedback spam

**Cleanup:**
- `cleanup_old_records()` function to prevent memory bloat
- Can be called periodically to remove stale records

### 2. Input Length Validation (`src/core/validation.py`)
Added `validate_text_length()` function:
- Takes text, field name, and max length
- Returns ValidationError if over limit
- Returns "ok" if under limit
- Handles None and empty strings gracefully

### 3. UI Input Limits (`src/ui/app.py`)
Added `max_chars` parameter to all text inputs:

| Field | Max Length |
|-------|-----------|
| Email | 254 chars |
| Password | 128 chars |
| Card nickname | 100 chars |
| Notes | 5000 chars |
| Feedback message | 10000 chars |
| Custom text input (extract card) | 50000 chars |
| URL input | 2000 chars |
| Retention offer details | 1000 chars |
| Product change notes | 1000 chars |
| Search field | 200 chars |
| SUB reward text | 200 chars |
| Spreadsheet import | 50000 chars |
| Delete confirmation | 50 chars |

**UI Layer (Streamlit `max_chars`):**
- Prevents casual overflows
- Immediate feedback to users
- Browser-side validation

**Server Layer (`validate_text_length`):**
- Second layer of defense
- Prevents API abuse
- Can be added to save handlers if needed

### 4. Integration Points

**Login Form:**
- Check rate limit before attempting login
- Record failed attempts
- Reset counter on success
- Show lockout message with remaining time

**Signup Form:**
- Check rate limit before registration
- Record signup attempt
- Show rate limit message

**Feedback Form:**
- Check rate limit before submission
- Record successful submissions
- Show rate limit message

### 5. Comprehensive Tests

**Rate Limiting Tests (`tests/test_auth.py`):**
- ✅ Login allows attempts under limit
- ✅ Login blocks after max attempts
- ✅ Login resets on success
- ✅ Signup allows attempts under limit
- ✅ Signup blocks after max attempts
- ✅ Feedback allows attempts under limit
- ✅ Feedback blocks after max attempts
- ✅ Lockout expires after timeout period

**Input Validation Tests (`tests/test_edge_cases.py`):**
- ✅ Text under limit passes
- ✅ Text at limit passes
- ✅ Text over limit fails with error
- ✅ None and empty strings pass
- ✅ All field types tested (email, password, nickname, notes, etc.)

**Test Results:**
```
67 passed, 28 warnings in 33.23s
```

All tests passing ✅

## Security Benefits

1. **Brute Force Protection:** Login rate limiting prevents password guessing attacks
2. **Signup Abuse Prevention:** Signup rate limiting prevents mass account creation
3. **Spam Prevention:** Feedback rate limiting prevents feedback spam
4. **DoS Prevention:** Input length limits prevent oversized payloads
5. **Database Protection:** Input limits prevent storage overflow
6. **Memory Protection:** Rate limiter cleanup prevents memory bloat

## Future Enhancements

1. **Redis/Memcached:** For distributed rate limiting across multiple servers
2. **IP-based tracking:** When deployed to infrastructure with IP access
3. **Progressive delays:** Exponential backoff instead of hard lockout
4. **Admin override:** Dashboard to manually reset rate limits
5. **Monitoring:** Track rate limit hits in StatusPulse

## Git Commit

Branch: `experiment`
Commit: `5367f30`
Message: "feat: Add rate limiting and input length limits"

Pushed to origin ✅

## Next Steps

1. ✅ Local testing (completed - all tests pass)
2. Deploy to experiment URL for staging tests
3. Smoke test the experiment deployment
4. JJ review and approval
5. Merge to main for production deployment

## Notes

- Rate limiter uses in-memory storage (module-level dicts)
- Works for single-instance deployments (Streamlit Cloud)
- For multi-instance deployments, replace with Redis
- Session ID fallback handles Streamlit Cloud IP limitations
- No breaking changes - all existing functionality preserved
