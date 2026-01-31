# ChurnPilot Execution Plan

**Created:** January 31, 2026  
**Status:** Active  
**Repo:** `hendrixAIDev/churn_copilot_hendrix`  
**Current branch:** `experiment` (active dev), `main` (localStorage, production)

---

## Codebase Snapshot

| Metric | Value |
|--------|-------|
| `app.py` (experiment) | 2,781 lines, 20+ functions |
| `app.py` (main) | 2,424 lines |
| `src/core/` modules | 21 files (auth, database, db_storage, demo, etc.) |
| `src/ui/components/` | 14 component files (mostly unused decorative) |
| Tests | 38 test files (many are browser/e2e that don't run in CI) |
| Diff main→experiment | +9,436 lines across 42 files |
| Core tests passing | 22/22 (test_database, test_db_storage, test_auth) |

---

## Phase 1: Foundation (Week 1–2) — "Make It Mergeable"

### 1.1 Clean Up Experiment Branch Before Merge
**Effort:** 3–4 hours | **Priority:** 🔴 Critical | **Dependencies:** None

- [ ] **Remove leaked secrets from ENVIRONMENTS.md** — Database passwords and API keys are committed in plaintext. Must be scrubbed from git history using `git filter-repo` or BFG Repo Cleaner before anyone else touches this repo.
  - Rotate ALL exposed passwords immediately (both Supabase instances)
  - Remove ENVIRONMENTS.md from tracking (add to .gitignore), keep as local-only reference
  - Scrub from git history
- [ ] **Audit .gitignore** — Ensure `.env`, `.env.local`, `.streamlit/secrets.toml` are all ignored
- [ ] **Delete `nul` file** — There's a stray file called `nul` in the repo root (Windows artifact)
- [ ] **Remove diagnostic scripts** — `diagnose_persistence.py`, `diagnose_storage.py`, `test_localstorage_minimal.py` are debugging leftovers

### 1.2 Merge Experiment → Main
**Effort:** 4–6 hours | **Priority:** 🔴 Critical | **Dependencies:** 1.1

Strategy: **Squash merge with feature flag**

- [ ] **Create feature flag for auth/DB mode:**
  ```python
  # In app.py or config
  USE_DATABASE = os.environ.get("USE_DATABASE", "false").lower() == "true"
  ```
  This lets main branch deploy with database OFF initially (existing localStorage behavior), then flip to database mode when ready.

- [ ] **Merge steps:**
  1. Create `merge-prep` branch from `experiment`
  2. Add feature flag wrapping auth/database code paths
  3. Test with flag OFF → confirms localStorage still works
  4. Test with flag ON → confirms database works
  5. PR from `merge-prep` → `main`
  6. Deploy to prod Streamlit Cloud with `USE_DATABASE=false` initially
  7. Flip flag to `true` after validation

- [ ] **Database migration for prod:**
  1. Run `init_database()` against prod Supabase (creates all 9 tables)
  2. Verify schema with `test_schema_health.py` pointed at prod
  3. No data migration needed (main branch has no persistent user data worth keeping)

- [ ] **Post-merge:** Set experiment branch to track main. Single branch going forward.

### 1.3 Test Suite Cleanup
**Effort:** 3–4 hours | **Priority:** 🟡 High | **Dependencies:** 1.2

The test directory has 38 files but most are browser-dependent or stale:

- [ ] **Keep (core tests):** `test_database.py`, `test_db_storage.py`, `test_auth.py`, `test_five_twenty_four.py`, `test_importer.py`, `test_library.py`, `test_normalize.py`, `test_periods.py`, `test_preferences.py`, `test_user_model.py`
- [ ] **Move to `tests/e2e/`:** `test_e2e_auth.py`, `test_e2e_cards.py`, `test_e2e_automated.py`, `test_e2e_with_logs.py`
- [ ] **Archive or delete:** `test_browser_persistence.py`, `test_bug_scenarios_browser.py`, `test_user_journeys_browser.py`, `test_web_storage.py`, `test_save_timing.py`, `test_session_persistence.py`, `test_minimal_save.py`, `test_add_card_save.py`, `test_add_card_working.py`, `test_immediate_check.py`, `test_persistence.py`, `test_persistence_stress.py`, `test_card_add_refresh.py` — these are localStorage debugging tests, irrelevant after DB migration
- [ ] **Add `pytest.ini` or `pyproject.toml`** with test markers:
  ```ini
  [pytest]
  markers =
      unit: Unit tests (no external deps)
      integration: Requires database connection
      e2e: End-to-end browser tests
  ```
- [ ] **Add GitHub Actions CI** — Run unit tests on every push (free tier: 2,000 min/month)

---

## Phase 2: Code Quality (Week 2–3) — "Break the Monolith"

### 2.1 Split app.py Into Modules
**Effort:** 6–8 hours | **Priority:** 🟡 High | **Dependencies:** 1.2

Current `app.py` is 2,781 lines with 20+ functions doing everything. Target structure:

```
src/ui/
├── app.py              # ~150 lines: main(), routing, page config
├── auth_ui.py          # ~200 lines: show_auth_page(), show_user_menu()
├── session.py          # ~120 lines: _save_session_token, _load_session_token, check_stored_session
├── sidebar.py          # ~200 lines: render_sidebar()
├── dashboard.py        # ~350 lines: render_dashboard(), render_empty_dashboard()
├── add_card.py         # ~550 lines: render_add_card_section(), render_extraction_result()
├── card_display.py     # ~400 lines: render_card_item(), render_card_edit_form()
├── action_required.py  # ~250 lines: render_action_required_tab()
├── five_twenty_four.py # ~120 lines: render_five_twenty_four_tab()
├── export.py           # ~70 lines: export_cards_to_csv()
├── styles.py           # ~100 lines: CUSTOM_CSS, get_issuer_color()
└── state.py            # ~50 lines: init_session_state()
```

**Approach:**
1. Extract `CUSTOM_CSS` and color functions → `styles.py`
2. Extract session/auth functions → `session.py`, `auth_ui.py`
3. Extract sidebar → `sidebar.py`
4. Extract card rendering → `card_display.py`
5. Extract add card flow → `add_card.py`
6. Extract dashboard → `dashboard.py`
7. Extract remaining tabs → individual files
8. `app.py` becomes thin orchestrator

Each extraction: move code → import → run tests → commit. One module at a time.

### 2.2 Clean Up src/ui/components/
**Effort:** 1–2 hours | **Priority:** 🟢 Medium | **Dependencies:** 2.1

The 14 component files (`bottom_sheet.py`, `celebration.py`, `hero.py`, `pull_to_refresh.py`, etc.) are mostly mobile-UI concepts that don't work well in Streamlit. 

- [ ] **Keep:** `celebration.py` (if used for SUB achievement), `empty_state.py`, `loading.py`, `toast.py`
- [ ] **Remove:** `bottom_sheet.py`, `pull_to_refresh.py`, `swipeable_card.py`, `touch_feedback.py`, `sticky_action_bar.py` — these are conceptual; Streamlit doesn't support these patterns
- [ ] **Evaluate:** `hero.py` (417 lines for a welcome section is excessive — simplify to ~50 lines)

### 2.3 Storage Layer Cleanup
**Effort:** 2–3 hours | **Priority:** 🟢 Medium | **Dependencies:** 1.2

- [ ] After database is live, deprecate `web_storage.py` and `storage.py` (JSON/localStorage)
- [ ] `DatabaseStorage` becomes the single storage backend
- [ ] Remove `streamlit-js-eval` dependency (only needed for localStorage)

---

## Phase 3: UX/UI Improvements (Week 3–4) — "Make It Not Ugly"

### 3.1 Visual Redesign with Streamlit Theming
**Effort:** 4–6 hours | **Priority:** 🟡 High | **Dependencies:** 2.1

Streamlit's built-in theming + targeted CSS is the way. Don't fight Streamlit.

- [ ] **Create `.streamlit/config.toml` theme:**
  ```toml
  [theme]
  primaryColor = "#2563EB"        # Blue-600
  backgroundColor = "#FFFFFF"
  secondaryBackgroundColor = "#F8FAFC"
  textColor = "#1E293B"
  font = "sans serif"
  ```

- [ ] **Dashboard cards redesign:**
  - Replace raw HTML card rendering with `st.container()` + `st.columns()` for consistency
  - Use `st.metric()` for key numbers (annual fee, SUB progress, credits used)
  - Color-coded status indicators via `st.status()` or styled badges
  - Issuer logos (small PNGs in `data/logos/`) displayed with `st.image()`

- [ ] **Simplify navigation:**
  - Current: sidebar with many options → overwhelming
  - Target: 4 main tabs: **Dashboard** | **Add Card** | **Tracking** | **Settings**
  - Use `st.tabs()` for main navigation instead of sidebar radio buttons

- [ ] **Mobile responsiveness:**
  - Streamlit is already responsive, but test card layouts on narrow screens
  - Use `st.columns([2,1])` patterns that collapse gracefully

### 3.2 Onboarding Flow
**Effort:** 3–4 hours | **Priority:** 🟡 High | **Dependencies:** 3.1

First-time users see an empty dashboard. Fix this:

- [ ] **Welcome wizard** (3 steps):
  1. "Welcome to ChurnPilot" — brief value prop
  2. "Add your first card" — choice of: paste URL, pick from library, manual entry
  3. "Set up tracking" — configure annual fee dates, SUB deadlines
- [ ] **Demo mode** — Show pre-populated dashboard with sample cards (use existing `demo.py`)
- [ ] **Empty states** — Every empty section gets a helpful illustration + CTA

### 3.3 AI Extraction UX Polish
**Effort:** 2–3 hours | **Priority:** 🟡 High | **Dependencies:** 2.1

The AI extraction pipeline is the product's moat. Make it feel magical:

- [ ] **Streaming feedback** — Show progress while Claude extracts ("Reading page... Extracting card details... Found: Chase Sapphire Preferred")
- [ ] **Preview before save** — Show extracted data in editable form, let user correct before saving
- [ ] **Confidence indicators** — Show which fields Claude was confident about vs. guessed
- [ ] **"Try it" demo** — Pre-loaded URL example so users can see extraction without their own data

---

## Phase 4: Monetization Prep (Week 4–5) — "Build the Gate"

### 4.1 User Tier System
**Effort:** 4–6 hours | **Priority:** 🟡 High | **Dependencies:** 1.2

- [ ] **Add `tier` column to users table:**
  ```sql
  ALTER TABLE users ADD COLUMN tier VARCHAR(20) DEFAULT 'free';
  ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255);
  ALTER TABLE users ADD COLUMN tier_expires_at TIMESTAMP;
  ```

- [ ] **Define tier limits:**
  | Feature | Free | Pro ($9.99/mo) |
  |---------|------|-----------------|
  | Cards tracked | 5 | Unlimited |
  | AI extractions/month | 3 | Unlimited |
  | Card library templates | All | All |
  | Benefit tracking | Basic | Full + reminders |
  | Export to CSV | ❌ | ✅ |
  | Retention offer tracking | ❌ | ✅ |
  | Product change tracking | ❌ | ✅ |

- [ ] **Add `ai_extractions` tracking table:**
  ```sql
  CREATE TABLE ai_extractions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID REFERENCES users(id),
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      card_url TEXT,
      tokens_used INTEGER
  );
  ```

- [ ] **Implement tier check middleware** — Check limits before allowing gated actions

### 4.2 Stripe Integration
**Effort:** 4–6 hours | **Priority:** 🟡 High | **Dependencies:** 4.1

- [ ] **Stripe account setup** (free)
- [ ] **Create product + price** ($9.99/mo recurring)
- [ ] **Checkout flow:**
  - User hits limit → "Upgrade to Pro" modal
  - Redirect to Stripe Checkout (hosted page — no PCI scope)
  - Webhook receives `checkout.session.completed` → update user tier
- [ ] **Webhook endpoint** — Can use Supabase Edge Functions (free tier) or a small FastAPI service
- [ ] **Cancel/downgrade flow** — Stripe Customer Portal link

**Note on Streamlit + Stripe:** Streamlit can't handle webhooks natively. Options:
1. **Supabase Edge Function** as webhook receiver (recommended — free, serverless)
2. **Poll-based:** Check Stripe API on user login for subscription status
3. **Separate FastAPI microservice** on free tier (Railway/Render)

### 4.3 Usage Tracking
**Effort:** 2–3 hours | **Priority:** 🟢 Medium | **Dependencies:** 4.1

- [ ] Track AI extraction count per user per month
- [ ] Track active users (DAU/MAU) — simple `last_login` column on users
- [ ] Basic analytics: which card templates are most popular, extraction success rate

---

## Phase 5: Launch Readiness (Week 5–6) — "Ship It"

### 5.1 Security Hardening
**Effort:** 3–4 hours | **Priority:** 🔴 Critical | **Dependencies:** 1.1

- [ ] **Rotate all exposed credentials** (Supabase passwords, API keys from ENVIRONMENTS.md)
- [ ] **Rate limiting** — Limit login attempts (5/min per IP), AI extractions (burst protection)
- [ ] **Input sanitization** — SQL injection is handled by psycopg2 parameterized queries ✅, but audit all raw text inputs
- [ ] **CSRF protection** — Streamlit handles this natively ✅
- [ ] **Session security** — Current 24h expiry is good. Add: logout invalidates token, expired session cleanup cron
- [ ] **Error handling** — Never expose stack traces or DB errors to users. Wrap all DB calls in try/except with user-friendly messages.

### 5.2 Performance & Reliability
**Effort:** 2–3 hours | **Priority:** 🟡 High | **Dependencies:** 2.1

- [ ] **Connection pooling** — Currently opens new connection per request. Add connection pool via `psycopg2.pool.ThreadedConnectionPool` or switch to `psycopg` (v3) with async pool
- [ ] **Caching** — Use `@st.cache_data` for card library templates, `@st.cache_resource` for DB connection pool
- [ ] **Error recovery** — Graceful handling when Supabase is down (show cached data, retry logic)
- [ ] **Streamlit Cloud limits** — Free tier: 1GB RAM, single worker. App sleeps after inactivity. Add loading state for cold starts.

### 5.3 Pre-Launch Checklist
**Effort:** 2–3 hours | **Priority:** 🔴 Critical | **Dependencies:** All above

- [ ] **Privacy policy** — Required for any app collecting user data. Use a generator + customize.
- [ ] **Terms of service** — Basic ToS covering: not financial advice, data handling, account deletion
- [ ] **Account deletion** — Users must be able to delete their account and all data (CASCADE deletes handle this in schema ✅)
- [ ] **Password reset flow** — Currently missing. Add email-based reset (or skip for MVP, provide manual reset via support)
- [ ] **README overhaul** — Current README is developer-focused. Create user-facing landing page / docs.
- [ ] **Custom domain** — `churnpilot.app` or similar ($12/year — worth it for credibility)
- [ ] **SEO / Landing page** — Simple page on `hendrixaidev.github.io` linking to the app

### 5.4 Beta Launch Strategy
**Effort:** Ongoing | **Priority:** 🟡 High | **Dependencies:** 5.3

- [ ] **Target communities:**
  - r/churning (660k members) — "I built a free tool for tracking churning"
  - r/creditcards (360k members)
  - Doctor of Credit comments
  - FlyerTalk forums
  - Credit card churning Facebook groups
- [ ] **Launch with free tier only** — Get users first, prove value, then add Pro
- [ ] **Feedback mechanism** — In-app feedback form (store in DB or Google Form)
- [ ] **Waitlist for Pro** — Collect emails for Pro launch notification

---

## Timeline Summary

| Phase | Weeks | Key Deliverable |
|-------|-------|-----------------|
| **1: Foundation** | 1–2 | Secrets rotated, experiment merged to main, tests cleaned |
| **2: Code Quality** | 2–3 | app.py split into modules, dead code removed |
| **3: UX/UI** | 3–4 | Visual redesign, onboarding flow, polished AI extraction |
| **4: Monetization** | 4–5 | Tier system, Stripe integration, usage tracking |
| **5: Launch** | 5–6 | Security hardened, landing page, beta launch to r/churning |

**Revenue Target:** $120/month by April 2026 = 12 Pro subscribers at $9.99/mo

---

## Critical Path (Do These First, In Order)

1. 🚨 **Rotate leaked credentials** (ENVIRONMENTS.md has plaintext passwords — do this TODAY)
2. 🔧 **Scrub secrets from git history**
3. 🔀 **Merge experiment → main** with feature flag
4. ✂️ **Split app.py** into modules
5. 🎨 **UX redesign** (theme + navigation + onboarding)
6. 💰 **Tier system + Stripe**
7. 🚀 **Beta launch on r/churning**

---

## Decisions Needed

1. **Password reset:** Email-based (need email provider) or skip for MVP?
2. **Webhook hosting:** Supabase Edge Functions vs separate microservice for Stripe?
3. **Free tier limits:** 5 cards + 3 AI extractions/month — too generous? Too stingy?
4. **Custom domain:** Worth $12/year before proving traction?
5. **Mobile app:** Stay Streamlit-only or plan for React Native later?

---

## Technical Debt to Track

- [ ] `demo.py` (277 lines) + `demo_components.py` (20k lines) — demo mode is over-engineered
- [ ] `enrichment.py` (13k) — needs review for accuracy and token efficiency  
- [ ] `web_storage.py` (11k) — entire file is dead code after DB migration
- [ ] `storage.py` (6k) — JSON storage, also dead after DB migration
- [ ] 14 UI components — most are mobile patterns that don't work in Streamlit
- [ ] No logging infrastructure — add structured logging before launch
- [ ] No error tracking — consider free Sentry tier (5k events/month)
