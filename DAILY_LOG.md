# ChurnPilot - Daily Development Log

**Purpose:** Capture story material for Chronicles while building  
**Format:** Use PROJECT_DOCUMENTATION_PROTOCOL.md template  

---

## 2026-01-31 - Local PostgreSQL Setup (Night Session)

### What I Attempted
- **Goal:** Set up local PostgreSQL database for faster iteration vs cloud
- **Approach:** Install PostgreSQL, create local DB, configure .env.local
- **Expected:** 30-45 minutes, smooth setup

### What Happened
- **Actual:** ~3 hours of environment variable loading complexity
- **Surprise:** Python module import order matters WAY more than expected
- **Blockers:** 
  - .env.local wouldn't override .env despite override=True
  - Cached .pyc files masked changes
  - Module import order meant env vars loaded in wrong sequence
- **Solution:** Created standalone `init_local_db.py` script that bypasses import chain

### The Struggle
- **Hard part:** Understanding why dotenv wasn't working despite following all docs
- **Frustration peak:** ~2 hours in, 10th attempt at env loading still using Supabase
- **Almost gave up:** Considered just sticking with remote DB (would have killed iteration speed)
- **Breakthrough:** Realized fighting Python imports = wrong battle. Standalone script = right answer.

### Metrics & Decisions
- **Time spent:** ~3 hours
- **Tokens used:** ~15K
- **Key decision:** Build init_local_db.py instead of "fixing" imports properly
- **Money spent:** $0 (PostgreSQL free, localhost)
- **Status:** 
  - ✅ 9 tables created in local DB
  - ✅ Streamlit app running locally
  - ⚠️ Still connecting to Supabase (env loading issue persists in app)
- **Next:** Fix app env loading or just update .env directly for local work

### Lessons Learned
- Sometimes brute force (standalone script) beats elegance (proper module system)
- Document blockers immediately - great Chronicle material
- 3 hours on dev tooling = many hours saved on iteration later
- Testing env vars: Clear Python cache FIRST, then test

### Chronicle Material
- 📝 **Quote:** "I spent 3 hours fighting Python imports to save hours later. This is the unglamorous 80% of building."
- 📝 **Contrast:** Expected 30 minutes → Took 3 hours (6x estimate!)
- 📝 **Lesson:** Developer tools enable speed, but setting them up costs time upfront
- 📝 **Emotion:** Frustration → almost quit → breakthrough relief
- 📝 **Universal truth:** The boring infrastructure work is what makes the exciting features possible

---

## Template for Future Entries

### What I Attempted
- Goal for this session:
- Approach I took:
- Expected outcome:

### What Happened
- Actual results:
- Surprises (good or bad):
- Blockers encountered:

### The Struggle
- What was hard:
- Moments of frustration:
- When I wanted to give up:
- Breakthrough moments:

### Metrics & Decisions
- Time spent:
- Tokens used:
- Key decisions made:
- Money spent:
- Code written:
- Tests passing:

### Lessons Learned
- What I learned:
- What I'd do differently:
- What I'll apply next time:

### Chronicle Material
- Most compelling moment:
- Quote-worthy insights:
- Emotional high/low points:
- Numbers that tell a story:
