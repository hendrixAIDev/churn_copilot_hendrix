# Session Persistence Analysis - Experiment Branch

**Date:** February 2, 2026  
**Source:** https://github.com/zrjaa1/churn_copilot/tree/experiment  
**Decision:** Adopt this approach for our ChurnPilot

---

## How It Works (Hybrid Database + localStorage)

### 1. Server-Side Session Management (Database)

**Database schema:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Session lifecycle:**
1. User registers/logs in → bcrypt password hashing
2. Server creates session token: `secrets.token_hex(32)` → 64-char hex string
3. Session stored in database with 24-hour expiry
4. Token returned to client

**Validation:**
- Check token exists in database
- Check `expires_at` not passed
- If valid, refresh expiry (sliding window: extends 24hr from now)
- Return user object or None

**Security:**
- Passwords bcrypt hashed (12 rounds)
- Session tokens cryptographically random (32 bytes)
- Expired sessions auto-cleaned on validation
- Max 5 active sessions per user (auto-prune oldest)

### 2. Client-Side Storage (localStorage)

**Token persistence:**
```javascript
// Save after login
localStorage.setItem('churnpilot_session', token);

// Load on app start
const token = localStorage.getItem('churnpilot_session');

// Clear on logout
localStorage.removeItem('churnpilot_session');
```

**Implementation:**
- Uses `streamlit_js_eval` library for reliable localStorage access
- Avoids Streamlit's iframe sandbox issue (our previous blocker)
- Also stores token in `st.session_state.session_token` for same-session access

**Auto-restore flow:**
```python
def _try_restore_session() -> bool:
    """Attempt to restore session from localStorage."""
    if st.session_state.get("_session_check_done"):
        return False
    
    token = _load_session_token()
    
    if token is None:
        return False
    
    # Validate against database
    user = auth.validate_session(token)
    
    if user:
        st.session_state.session_token = token
        st.session_state.current_user = user
        st.session_state._session_check_done = True
        return True
    else:
        _clear_session_token()  # Invalid token
        return False
```

### 3. Why This Works (vs. Our Previous Attempts)

**Our previous issue:**
- Tried to set cookies from Streamlit components
- All components run in sandboxed iframes
- Couldn't write to parent page's cookies or localStorage

**Experiment branch solution:**
- Uses `streamlit_js_eval` library
- This library has special access to parent page context
- Can read/write localStorage reliably
- Not blocked by iframe sandbox

**Key libraries:**
```python
# requirements.txt
streamlit-js-eval==0.1.5  # For localStorage access
bcrypt>=4.0.1             # Password hashing
psycopg2-binary>=2.9.9    # PostgreSQL adapter
```

---

## Implementation Plan for Our ChurnPilot

### Phase 1: Database Setup (30 min)

1. **Add migrations for users + sessions tables**
   - Create `migrations/003_add_auth_tables.sql`
   - Run against our Supabase production database

2. **Install dependencies**
   ```bash
   pip install streamlit-js-eval bcrypt
   ```

### Phase 2: Auth Module (1 hour)

1. **Port `src/core/auth.py` from experiment branch**
   - Copy AuthService class
   - Adapt to our existing database connection pattern
   - Keep all security features (bcrypt, session expiry, token generation)

2. **Port `src/core/models.py` User model**
   - Simple dataclass for user data

### Phase 3: UI Integration (1 hour)

1. **Create login/register screens**
   - Simple email + password forms
   - Form validation (email format, password length)
   - Error messaging

2. **Add session restoration logic**
   - Check localStorage on app start
   - Auto-login if valid session exists
   - Clear invalid sessions

3. **Update card storage to be user-scoped**
   - Add `user_id` foreign key to cards table
   - Filter all queries by current user
   - Migrate existing test data

### Phase 4: Testing (30 min)

1. **Local testing:**
   - Register → login → add card → refresh → still logged in
   - Logout → session cleared
   - Session expiry (mock 24hr forward)

2. **Deploy to Streamlit Cloud**
   - Test on live URL
   - Verify localStorage works on deployed version
   - Smoke test full user journey

---

## Advantages Over Current Approach

| Feature | Current (`st.query_params`) | Experiment (DB + localStorage) |
|---------|----------------------------|-------------------------------|
| **Survives refresh** | ✅ If URL has `?s=` token | ✅ Always (localStorage) |
| **Survives typed URL** | ❌ Need `?s=` param | ✅ Token in browser storage |
| **Survives bookmark** | ⚠️ Shares session | ✅ Token in browser storage |
| **Security** | ⚠️ Token in URL (visible) | ✅ Token in localStorage (hidden) |
| **Session expiry** | ❌ No server-side validation | ✅ 24hr with sliding window |
| **Multi-device** | ❌ URL-bound | ✅ Login from any device |
| **Logout** | ❌ Just clear URL param | ✅ Server deletes session |
| **Sharing URLs** | ⚠️ Shares session | ✅ Safe (no token in URL) |

---

## Migration Strategy

**Option A: Clean Break (Recommended)**
1. Deploy new auth system alongside old
2. Add banner: "Please re-register to use the new version"
3. Keep old data accessible but read-only
4. Sunset old system after 30 days

**Option B: Token Migration**
1. Generate unique email for each old session token
2. Create user accounts automatically
3. Map old cards to new user_id
4. Risky: users don't know their auto-generated emails

**Recommendation:** Option A. We have zero users currently, so clean break is safe.

---

## Files to Create/Modify

### New Files:
- `migrations/003_add_auth_tables.sql`
- `src/core/auth.py`
- `src/core/models.py` (User model)
- `tests/test_auth.py`
- `tests/test_session_persistence.py`

### Modified Files:
- `requirements.txt` (add streamlit-js-eval, bcrypt)
- `src/ui/app.py` (add login/register screens, session restore)
- `src/core/database.py` (ensure compatible with auth module)
- `migrations/001_initial_schema.sql` (add user_id FK to cards)

### Estimated Effort:
- **Phase 1 (DB setup):** 30 min
- **Phase 2 (Auth module):** 1 hour
- **Phase 3 (UI integration):** 1 hour
- **Phase 4 (Testing):** 30 min
- **Total:** 3 hours

---

## Decision: ADOPT

This is the right solution for ChurnPilot session persistence. It:
- ✅ Solves the UX problem (no more lost sessions)
- ✅ Uses battle-tested libraries (bcrypt, streamlit-js-eval)
- ✅ Adds proper authentication (future-proofs for multi-user)
- ✅ Works within Streamlit's constraints (no iframe sandbox issues)
- ✅ Is production-ready (experiment branch has comprehensive tests)

**Next Step:** Add to Priority 2 in today's execution plan and implement.
