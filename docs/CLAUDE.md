# ChurnPilot

AI-powered credit card churning management system.

## Architecture

```
src/
├── core/           # Framework-agnostic business logic
│   ├── web_storage.py  # Browser localStorage (THE PROBLEM AREA)
│   ├── models.py       # Pydantic data models
│   └── extractor.py    # AI extraction
└── ui/
    └── app.py          # Streamlit UI (2300 lines)
```

## Permissions

Full workspace autonomy granted:
- Create, modify, delete files
- Git operations (no force push without approval)
- Run tests and scripts
- Install dependencies

## Current Issue

**Data persistence bug** - See `docs/claude-guides/current-bug.md`

## Detailed Guides (load only when relevant)

| Guide | When to Load |
|-------|--------------|
| `docs/claude-guides/current-bug.md` | Working on the persistence bug |
| `docs/claude-guides/testing.md` | Running tests, verification |
| `docs/claude-guides/debugging.md` | Fixing bugs |
| `docs/claude-guides/streamlit-gotchas.md` | Streamlit-specific issues |
| `docs/claude-guides/coding-standards.md` | Writing new code |
| `docs/claude-guides/autonomous-mode.md` | User requests autonomous work |

## Quick Commands

```bash
# Run app
streamlit run src/ui/app.py

# Run tests
python -m pytest tests/test_web_storage.py -v

# Verify imports
python -c "from src.core.web_storage import WebStorage"
```

## Key Insight

**Unit tests pass but bug persists** = tests aren't testing real user behavior.
Must verify in actual browser with F12 > Application > Local Storage.
