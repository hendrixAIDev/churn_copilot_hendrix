# ChurnPilot - Deployment Guide

## Quick Deploy to Streamlit Cloud (2 minutes)

### Prerequisites
✅ All done! Database, API keys, and code are ready.

### Steps

1. **Go to** https://share.streamlit.io
2. **Sign in** with your GitHub account (hendrixAIDev)
3. **Click** "New app"
4. **Select:**
   - Repository: `hendrixAIDev/churn_copilot_hendrix`
   - Branch: `main`
   - Main file path: `src/ui/app.py`
5. **Click** "Deploy!"

**That's it!** Streamlit will:
- Install dependencies from `requirements.txt`
- Pull secrets from your `.env` file (need to add them in Streamlit UI)
- Launch the app at `https://<your-app>.streamlit.app`

### Adding Secrets in Streamlit Cloud

After deployment, go to Settings → Secrets and paste:

```toml
SUPABASE_URL = "https://fphvunzlxaebwphjsaeu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwaHZ1bnpseGFlYndwaGpzYWV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg5NjE5OTIsImV4cCI6MjA1NDUzNzk5Mn0.9ZE6l4S2GKdwNuPP4eoHT__4Jz2a4Gr7lHJC5jCHKSA"
CLAUDE_API_KEY = "sk-ant-api03-bnW6snYk7Y4i7lY6lUfpqcT1R_kQbrgMVKQg3LN5__PN3WjBWFBK5H3tqFqzlzNKLq6SxzRR3X7kXIjQ5R5BuA-MUosFAAA"
```

### Alternative: Manual Deploy with Render

If Streamlit Cloud continues to have issues:

1. Go to https://render.com
2. Sign in with GitHub
3. Create new "Web Service"
4. Select `churn_copilot_hendrix` repo
5. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run src/ui/app.py --server.port=$PORT --server.address=0.0.0.0`
   - **Environment variables:** Add SUPABASE_URL, SUPABASE_KEY, CLAUDE_API_KEY

---

## Current Status

✅ **Complete:**
- Supabase database (9 tables)
- Authentication system
- Core business logic
- Local testing successful (22/22 tests passing)
- Streamlit UI working locally

⏸️ **Pending:**
- Deploy to cloud (blocked by Streamlit Cloud auth issues)
- Can be completed manually in 2 minutes via web UI

## Testing Locally

```bash
cd /Users/hendrix/.openclaw/workspace/churn_copilot_hendrix
source venv/bin/activate
streamlit run src/ui/app.py
```

Visit http://localhost:8501

## Next Steps After Deployment

1. Register a test user
2. Add test credit cards
3. Verify spend tracking
4. Test AI optimization recommendations
5. Gather feedback from real usage
