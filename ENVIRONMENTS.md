# ChurnPilot Environment Configuration

**Established:** January 31, 2026  
**Author:** JJ (directive) + Hendrix (implementation)

---

## Three Environments

### 1. Local Dev → Sandbox Supabase
- **Purpose:** Local development and testing
- **Config method:** `.env` / `.env.local` file (gitignored) + `.streamlit/secrets.toml` (gitignored)
- **Database:** Sandbox Supabase (ChurnPilot project)
- **Branch:** Any (local work)
- **Connection:** Transaction Pooler mode

### 2. Remote Experiment → Sandbox Supabase
- **Purpose:** Testing code with Streamlit Cloud integration before prod
- **Config method:** Streamlit Cloud app → Settings → Secrets (NOT .env)
- **Database:** Sandbox Supabase (same instance as local dev)
- **Branch:** `experiment`
- **Flow:** Test here before pushing to prod

### 3. Production → Production Supabase
- **Purpose:** Live product for real users
- **Config method:** Streamlit Cloud app → Settings → Secrets (NOT .env)
- **Database:** Production Supabase (dedicated instance)
- **Branch:** `main` (or dedicated `prod` branch)

---

## Key Rules

1. **`.env` is local-only.** Never use it for remote environments.
2. **Streamlit Secrets for remote.** Both experiment and prod use Streamlit's built-in secrets management.
3. **Test in experiment first.** Code goes: local → experiment remote → prod.
4. **Separate Supabase instances.** Sandbox (local + experiment) vs Production (prod).
5. **Transaction Pooler mode.** All connections use Transaction Pooler (IPv4 compatible, port 6543).

---

## Supabase Instances

### Sandbox (Local Dev + Experiment)
- **Project name:** ChurnPilot
- **Project ID:** `iwekqsxshzadzxezkrxo`
- **Region:** AWS us-west-2 (Oregon)
- **Project URL:** `https://iwekqsxshzadzxezkrxo.supabase.co`
- **Transaction Pooler:** `postgresql://postgres.iwekqsxshzadzxezkrxo:[PASSWORD]@aws-0-us-west-2.pooler.supabase.com:6543/postgres`
- **API Key:** `sb_publishable_N7O4-2WoIZKO0rjxo8vp6A_LxgXQsGM`

### Production
- **Project name:** ChurnPilot-Prod
- **Project ID:** `qgrkmsvblpfjkcjdwwdo`
- **Region:** AWS us-west-2 (Oregon)
- **Project URL:** `https://qgrkmsvblpfjkcjdwwdo.supabase.co`
- **Transaction Pooler:** `postgresql://postgres.qgrkmsvblpfjkcjdwwdo:[PASSWORD]@aws-0-us-west-2.pooler.supabase.com:6543/postgres`
- **API Key:** `sb_publishable_5RON6hgfS0BsFT1Ek8N0MQ_iVIjnKbk`

---

## Streamlit Secrets Format (for remote environments)

Set in Streamlit Cloud → App → Settings → Secrets:

```toml
DATABASE_URL = "postgresql://postgres.PROJECT_ID:PASSWORD@aws-0-us-west-2.pooler.supabase.com:6543/postgres"
ANTHROPIC_API_KEY = "sk-ant-..."
```

### Experiment App Secrets
```toml
DATABASE_URL = "postgresql://postgres.iwekqsxshzadzxezkrxo:REDACTED_SANDBOX_PW@aws-0-us-west-2.pooler.supabase.com:6543/postgres"
ANTHROPIC_API_KEY = "sk-ant-api03-..."
```

### Prod App Secrets (when deploying)
```toml
DATABASE_URL = "postgresql://postgres.qgrkmsvblpfjkcjdwwdo:REDACTED_PROD_PW@aws-0-us-west-2.pooler.supabase.com:6543/postgres"
ANTHROPIC_API_KEY = "sk-ant-api03-..."
```
