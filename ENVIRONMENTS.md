# ChurnPilot Environment Configuration

**Established:** January 31, 2026  
**Author:** JJ (directive) + Hendrix (implementation)

---

## Three Environments

### 1. Local Dev → Sandbox Supabase
- **Purpose:** Local development and testing
- **Config method:** `.env` file (gitignored)
- **Database:** Sandbox Supabase instance
- **Branch:** Any (local work)
- **Notes:** `.env` is ONLY for local environment. Never commit.

### 2. Remote Experiment → Sandbox Supabase
- **Purpose:** Testing code with Streamlit Cloud integration before prod
- **Config method:** Streamlit app → Settings → Secrets (NOT .env)
- **Database:** Sandbox Supabase instance (same as local dev)
- **Branch:** `experiment`
- **Flow:** Test here before pushing to prod
- **Secret format in Streamlit:**
  ```toml
  DATABASE_URL = "postgresql://postgres:password@db.supabase.co:5432/postgres"
  ```

### 3. Production → Production Supabase
- **Purpose:** Live product for real users
- **Config method:** Streamlit app → Settings → Secrets (NOT .env)
- **Database:** Production Supabase instance (separate from sandbox)
- **Branch:** `main` (or dedicated `prod` branch)
- **Secret format in Streamlit:**
  ```toml
  DATABASE_URL = "postgresql://postgres:password@db.prod-supabase.co:5432/postgres"
  ```

---

## Key Rules

1. **`.env` is local-only.** Never use it for remote environments.
2. **Streamlit Secrets for remote.** Both experiment and prod use Streamlit's built-in secrets management.
3. **Test in experiment first.** Code goes: local → experiment remote → prod.
4. **Separate Supabase instances.** Sandbox (dev + experiment) vs Production (prod).

---

## Current Supabase Instances

### Sandbox (Dev + Experiment)
- **Project:** ChurnPilot
- **URL:** `https://iwekqsxshzadzxezkrxo.supabase.co`
- **Connection:** `postgresql://postgres:[password]@db.iwekqsxshzadzxezkrxo.supabase.co:5432/postgres`

### Production
- **TBD** — Will create when ready to launch
