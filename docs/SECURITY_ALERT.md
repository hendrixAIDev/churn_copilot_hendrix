# SECURITY ALERT: PostgreSQL URI Exposed on GitHub

## Status: NEEDS ATTENTION

**Source:** GitGuardian email alert (Jan 31, 2026 12:01 PM)
**Repository:** hendrixAIDev/churn_copilot_hendrix
**Secret type:** PostgreSQL URI (Supabase connection strings)

## What Happened
- During early development, Supabase connection strings (including project IDs and passwords) were committed to git history
- Although later commits redacted the passwords, the URIs remain in git history
- GitGuardian detected and flagged this

## Affected Resources
- Supabase project: qgrkmsvblpfjkcjdwwdo (ChurnPilot-Prod)
- Supabase project: iwekqsxshzadzxezkrxo (ChurnPilot-Sandbox)

## Required Actions
1. **Rotate Supabase database passwords** for both projects
   - Go to Supabase Dashboard > Project Settings > Database > Reset database password
   - Update .env and .streamlit/secrets.toml locally with new passwords
   - Update Streamlit Cloud secrets
2. **Consider using BFG Repo Cleaner** to scrub git history
   - `bfg --replace-text passwords.txt churn_copilot_hendrix.git`
3. **Dismiss the GitGuardian alert** after passwords are rotated

## Risk Assessment
- LOW-MEDIUM: The passwords were partially redacted in some commits
- The Supabase projects use Row Level Security (RLS) which limits exposure
- No sensitive user data in the database (only test accounts)
- Still, best practice is to rotate credentials ASAP

## Prevention
- Always use environment variables for secrets
- Never commit .env or secrets.toml (already in .gitignore)
- Pre-commit hooks for secret scanning (consider git-secrets or gitleaks)
