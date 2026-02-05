# Platform Independence Audit: ChurnPilot

**Date:** 2025-01-31  
**Auditor:** Subagent (Architecture Review)  
**Scope:** `projects/churn_copilot/app/src/` (22 core files, 17 UI files, 2713-line main UI)

---

## Executive Summary

**Current State:** ChurnPilot is **moderately coupled** to Streamlit and **lightly coupled** to PostgreSQL/Supabase. The codebase has a clean separation between `src/core/` (business logic) and `src/ui/` (presentation), but several **critical violations** compromise platform independence.

**Migration Difficulty:**
- **Streamlit → Flask/FastAPI:** 6/10 (doable but painful)
- **Supabase → SQLite:** 4/10 (relatively easy)

**Primary Risk:** Business logic files import Streamlit for secrets management and session state, creating unnecessary coupling. A Flask migration would require rewriting these files.

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                    │
│  (src/ui/app.py - 2713 lines + 16 component files)      │
│  • Renders UI                                             │
│  • Handles user input                                     │
│  • Calls core business logic                             │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Core Business Logic Layer                   │
│              (src/core/ - 22 modules)                    │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │  pipeline    │  │  enrichment  │  │  five_twenty   │ │
│  │  fetcher     │  │  importer    │  │  _four         │ │
│  │  preprocessor│  │  library     │  │  periods       │ │
│  │  normalize   │  │  models      │  │  validation    │ │
│  │  exceptions  │  └──────────────┘  └────────────────┘ │
│  └─────────────┘                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Storage Abstraction (Good!)               │   │
│  │  ┌────────────┐  ┌─────────────┐                 │   │
│  │  │ storage.py │  │web_storage  │ <-- VIOLATIONS! │   │
│  │  │ (file)     │  │(streamlit)  │                 │   │
│  │  └────────────┘  └─────────────┘                 │   │
│  │  ┌─────────────────────────────┐                 │   │
│  │  │    DatabaseStorage          │                 │   │
│  │  │    (PostgreSQL)             │                 │   │
│  │  └─────────────────────────────┘                 │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                 Data Persistence                         │
│  • PostgreSQL (via psycopg2) <-- Coupled via SQL        │
│  • Browser localStorage (via streamlit_js_eval)         │
│  • JSON files (platform-independent ✓)                  │
└─────────────────────────────────────────────────────────┘
```

**Good Architecture Decisions:**
- ✅ Clean separation: `src/core/` vs `src/ui/`
- ✅ Storage abstraction: `storage.py`, `web_storage.py`, `db_storage.py`
- ✅ Business logic mostly in `core/` (extraction, enrichment, validation, etc.)
- ✅ Pydantic models for data validation (`models.py`)

**Bad Architecture Decisions:**
- ❌ Streamlit imports in core business logic files
- ❌ Hardcoded `st.secrets` for config (should use env vars)
- ❌ `web_storage.py` uses `st.session_state` (belongs in UI layer)
- ❌ Auth relies on PostgreSQL-specific SQL (not abstracted)

---

## Coupling Violations

### CRITICAL (Severity: 10/10)

#### 1. **web_storage.py: Entire module is Streamlit-locked**
**File:** `src/core/web_storage.py`  
**Lines:** 1, 20, 25, 75-100, 114-130  
**Description:**  
This is a **core business logic file** that imports and heavily uses:
- `import streamlit as st`
- `st.session_state` (lines 75, 78, 79, 81, 83, 84, 88, 92, 152-156, 192-197)
- `st.query_params` (line not visible, likely in session management)
- `st.toast()` (line 88)
- `streamlit_js_eval` (lines 25, 75, 114)

**Impact:**  
This module **cannot be used** in Flask, FastAPI, or CLI environments. It's a storage backend, so it's called by all card operations, making the entire app Streamlit-dependent at the storage layer.

**Why this is bad:**  
Storage backends should be framework-agnostic. Session state and toasts belong in the UI layer, not the storage layer.

**Fix Difficulty:** High (requires refactoring to separate storage logic from UI state management)

---

#### 2. **database.py: Streamlit secrets for config**
**File:** `src/core/database.py`  
**Lines:** 22-26  
**Description:**
```python
try:
    import streamlit as st
    url = st.secrets.get("DATABASE_URL")
    if url:
        return url
except Exception:
    pass
```

**Impact:**  
Core database module tries Streamlit secrets first, falls back to env vars. This means:
- Database connection is Streamlit-aware
- Flask/FastAPI would need to remove this code or have Streamlit installed

**Why this is bad:**  
Config loading should use **environment variables first**, with optional platform-specific overrides in the UI layer.

**Fix Difficulty:** Low (reverse priority: env vars first, then platform-specific overrides)

---

#### 3. **pipeline.py: Streamlit secrets for API keys**
**File:** `src/core/pipeline.py`  
**Lines:** 134-138  
**Description:**
```python
try:
    import streamlit as st
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
except:
    pass
```

**Impact:**  
AI extraction pipeline (core feature) checks Streamlit secrets before env vars. Same coupling as #2.

**Fix Difficulty:** Low (reverse priority order)

---

#### 4. **importer.py: Streamlit secrets for API keys**
**File:** `src/core/importer.py`  
**Lines:** 46-49  
**Description:**  
Same pattern as pipeline.py — tries `st.secrets` first for `ANTHROPIC_API_KEY`.

**Fix Difficulty:** Low

---

### HIGH (Severity: 8/10)

#### 5. **db_storage.py: Raw PostgreSQL SQL**
**File:** `src/core/db_storage.py`  
**Lines:** Entire file (300+ lines of raw SQL)  
**Description:**  
All database operations use raw PostgreSQL-specific SQL via `psycopg2`:
- `cursor.execute("INSERT INTO cards ...")`
- Uses PostgreSQL-specific features: `RETURNING`, `ON CONFLICT`, `CURRENT_TIMESTAMP`
- 10+ tables with complex JOINs

**Impact:**  
Cannot swap to SQLite, MySQL, or any other database without rewriting all SQL.

**Why this is bad:**  
No ORM abstraction (SQLAlchemy, Django ORM, etc.). PostgreSQL-specific syntax blocks portability.

**Fix Difficulty:** Medium-High (rewrite with SQLAlchemy Core or ORM)

---

#### 6. **auth.py: Raw PostgreSQL SQL**
**File:** `src/core/auth.py`  
**Lines:** Throughout (300+ lines)  
**Description:**  
Same as db_storage.py — uses raw `psycopg2` with PostgreSQL-specific SQL for user management, sessions, password hashing.

**Fix Difficulty:** Medium-High

---

### MEDIUM (Severity: 5/10)

#### 7. **preferences.py: File-based storage**
**File:** `src/core/preferences.py`  
**Lines:** Entire file  
**Description:**  
Uses JSON file storage (`data/preferences.json`). Works locally but **not on Streamlit Cloud** (ephemeral filesystem). Should use database or localStorage.

**Impact:**  
Preferences don't persist on cloud deployments.

**Fix Difficulty:** Low (add `DatabaseStorage` backend for preferences)

---

### LOW (Severity: 3/10)

#### 8. **storage.py: Local file system**
**File:** `src/core/storage.py`  
**Lines:** Entire file  
**Description:**  
JSON file-based storage (`data/cards.json`). Platform-independent but ephemeral on Streamlit Cloud.

**Impact:**  
Only usable for local development. Cloud deployments must use `DatabaseStorage` or `WebStorage`.

**Fix Difficulty:** None (this is a valid fallback for local dev)

---

## Architectural Anti-Patterns

### 1. **Business Logic in UI Layer (Moderate)**
**File:** `src/ui/app.py` (2713 lines)  
**Evidence:**  
- Session management logic mixed with UI rendering
- Data transformations in render functions
- Validation logic in form handlers

**Impact:**  
Makes it harder to extract business logic for API/CLI reuse.

**Recommendation:**  
Move session management, validation, and transformations to `src/core/`.

---

### 2. **Storage Layer Tied to UI Framework (Critical)**
**See Violation #1** — `web_storage.py` should not use `st.session_state`.

---

### 3. **Config Management Inverted (High)**
**Pattern observed:**  
```python
# WRONG (current)
try:
    import streamlit as st
    api_key = st.secrets.get("KEY")
except:
    api_key = os.getenv("KEY")

# RIGHT (platform-independent)
api_key = os.getenv("KEY")
if not api_key and streamlit_available():
    api_key = st.secrets.get("KEY")
```

**Fix:** Create a `src/core/config.py` module that reads env vars first, with platform-specific overrides in `src/ui/` if needed.

---

## Migration Difficulty Scores

### Streamlit → Flask/FastAPI (6/10)

**What needs to change:**

| Component | Effort | Reason |
|-----------|--------|--------|
| `web_storage.py` | **HIGH** | Remove all `st.session_state`, `st.toast`, `streamlit_js_eval`. Replace with Flask sessions or Redis. |
| `database.py`, `pipeline.py`, `importer.py` | **LOW** | Reverse config priority (env vars first). |
| `src/ui/app.py` | **HIGH** | Complete rewrite (2713 lines → Flask routes + Jinja templates). |
| Session management | **MEDIUM** | Replace Streamlit's `st.query_params` with Flask-Login or JWT tokens. |
| UI components | **HIGH** | 16 Streamlit component files → rewrite in HTML/CSS/JS. |

**Total Effort:** ~3-4 weeks for a competent team.

**Blockers:**
- `web_storage.py` is tightly coupled to Streamlit's state management
- UI is 100% Streamlit-specific (no shared templates)

**Recommendation:**  
If migrating to Flask/FastAPI, create a **storage adapter interface** and implement Flask-specific backends (Redis, database sessions, etc.).

---

### Supabase/PostgreSQL → SQLite (4/10)

**What needs to change:**

| Component | Effort | Reason |
|-----------|--------|--------|
| `db_storage.py` | **MEDIUM** | Rewrite SQL to remove `RETURNING`, `ON CONFLICT`. Use SQLAlchemy instead. |
| `auth.py` | **MEDIUM** | Same as above. |
| `database.py` | **LOW** | Replace `psycopg2` with `sqlite3` (Python stdlib). |
| Schema | **LOW** | Convert PostgreSQL schema to SQLite (remove `UUID`, `gen_random_uuid()`). |

**Total Effort:** ~1-2 weeks.

**Blockers:**
- Raw SQL throughout (no ORM)
- PostgreSQL-specific features (`RETURNING`, `ON CONFLICT`, `UUID`)

**Recommendation:**  
Refactor to **SQLAlchemy Core** for database-agnostic SQL. This makes SQLite, MySQL, and PostgreSQL all equally viable.

---

## Recommended Refactoring Steps (Prioritized)

### Phase 1: Decouple Config (1 day)
**Priority:** HIGH  
**Impact:** Immediate — removes Streamlit imports from 3 core modules

1. Create `src/core/config.py`:
   ```python
   import os
   
   def get_secret(key: str, default=None):
       """Get secret from env vars (Streamlit-agnostic)."""
       return os.getenv(key, default)
   ```

2. Replace all `st.secrets.get()` in core modules with `config.get_secret()`.

3. In `src/ui/app.py`, override with Streamlit secrets **only** if needed:
   ```python
   # UI layer can inject Streamlit secrets into env
   if "ANTHROPIC_API_KEY" not in os.environ:
       os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
   ```

**Result:** `database.py`, `pipeline.py`, `importer.py` no longer import Streamlit.

---

### Phase 2: Refactor web_storage.py (3 days)
**Priority:** CRITICAL  
**Impact:** Makes storage layer framework-agnostic

1. Rename `web_storage.py` → `streamlit_storage.py` (acknowledge it's Streamlit-specific).

2. Create `src/core/session_storage.py` (abstract interface):
   ```python
   class SessionStorageBackend(ABC):
       @abstractmethod
       def get_data(self) -> list[dict]: ...
       
       @abstractmethod
       def set_data(self, data: list[dict]): ...
   ```

3. Implement `StreamlitSessionBackend(SessionStorageBackend)` in `src/ui/storage_backends.py`.

4. Move **all Streamlit imports** to the UI layer.

**Result:** Core storage logic is reusable; Streamlit-specific parts are in `src/ui/`.

---

### Phase 3: Add ORM for Database (5 days)
**Priority:** HIGH  
**Impact:** Makes database swappable (SQLite, MySQL, PostgreSQL)

1. Install SQLAlchemy: `pip install sqlalchemy`

2. Define models in `src/core/db_models.py` (SQLAlchemy ORM):
   ```python
   from sqlalchemy import Column, String, Integer, ForeignKey
   from sqlalchemy.ext.declarative import declarative_base
   
   Base = declarative_base()
   
   class Card(Base):
       __tablename__ = "cards"
       id = Column(String, primary_key=True)
       name = Column(String, nullable=False)
       # ...
   ```

3. Refactor `db_storage.py` to use SQLAlchemy queries instead of raw SQL.

4. Create `src/core/database_factory.py` to support multiple backends:
   ```python
   def get_engine(db_url: str):
       return create_engine(db_url)  # Works with sqlite://, postgresql://, etc.
   ```

**Result:** Database backend is swappable via `DATABASE_URL` env var.

---

### Phase 4: Extract Business Logic from UI (3 days)
**Priority:** MEDIUM  
**Impact:** Enables API/CLI reuse

1. Move validation logic from `app.py` to `src/core/validation.py` (already exists, expand it).

2. Move session management helpers to `src/core/auth.py` or new `src/core/session.py`.

3. Keep only **rendering** in `app.py` — all business logic should call `core/` modules.

**Result:** `core/` is now CLI-runnable, API-ready.

---

### Phase 5: Create Platform Adapter Pattern (Optional, 2 days)
**Priority:** LOW  
**Impact:** Future-proofs for multi-platform deployment

1. Create `src/adapters/` for framework-specific code:
   ```
   src/adapters/
   ├── streamlit_adapter.py   # Streamlit-specific UI helpers
   ├── flask_adapter.py        # Future Flask routes
   └── cli_adapter.py          # Future CLI commands
   ```

2. Move all Streamlit imports to `streamlit_adapter.py`.

3. Core modules call adapter interfaces, not framework APIs directly.

**Result:** Core is 100% framework-agnostic.

---

## Risk Assessment

### If Migration Happens Tomorrow

**To Flask/FastAPI:**
- ❌ **Blocked** by `web_storage.py` (needs 3-5 day refactor)
- ⚠️ **Painful** — 2713-line UI must be rewritten
- ✅ **Business logic mostly portable** (extraction, enrichment, validation)

**To SQLite:**
- ⚠️ **Doable** but tedious (raw SQL rewrite)
- ✅ **Schema is simple** (10 tables, straightforward)
- ❌ **No ORM** — must manually port PostgreSQL-specific SQL

---

## Conclusion

ChurnPilot has **good bones** (clean `core/` vs `ui/` separation) but suffers from **leaky abstraction** — Streamlit has infiltrated the business logic layer via:
1. **Config management** (secrets)
2. **Storage layer** (session state)
3. **UI feedback** (toasts in storage module)

**Migration is possible but not trivial.** The codebase is ~70% platform-independent (business logic is solid), but the remaining 30% (storage + config) creates hard dependencies.

**Priority fix:** Decouple `web_storage.py` from Streamlit (Phase 2). This is the single biggest blocker to portability.

**Timeline estimate:**
- **Quick fixes** (config decoupling): 1-2 days
- **Full platform independence**: 2-3 weeks
- **Flask migration**: 4-6 weeks (UI rewrite is the bottleneck)

---

## Appendix: File-by-File Coupling Summary

| File | Streamlit Imports? | DB-Specific? | Severity |
|------|-------------------|--------------|----------|
| `web_storage.py` | ✅ (heavy) | ❌ | CRITICAL |
| `database.py` | ✅ (secrets) | ✅ PostgreSQL | HIGH |
| `pipeline.py` | ✅ (secrets) | ❌ | HIGH |
| `importer.py` | ✅ (secrets) | ❌ | HIGH |
| `db_storage.py` | ❌ | ✅ PostgreSQL | HIGH |
| `auth.py` | ❌ | ✅ PostgreSQL | HIGH |
| `preferences.py` | ❌ | ❌ (file) | MEDIUM |
| `storage.py` | ❌ | ❌ (file) | LOW |
| All other `core/` | ❌ | ❌ | ✅ Clean |
| `ui/app.py` | ✅ (intentional) | ❌ | N/A (UI layer) |

**Legend:**
- ✅ = Coupled
- ❌ = Independent
- CRITICAL = Blocks migration
- HIGH = Significant effort to fix
- MEDIUM = Moderate effort
- LOW = Minor or acceptable coupling

---

**End of Audit**
