# ChurnPilot - Development Guidelines

## Project Overview

ChurnPilot is an AI-powered credit card churning management system. The architecture prioritizes **modularity** to allow UI framework swaps (Streamlit → React) without touching core business logic.

## Architecture Principles

### Separation of Concerns

```
src/
├── core/           # Framework-agnostic business logic
│   ├── extractor.py    # AI extraction (Anthropic API)
│   ├── models.py       # Pydantic data models
│   └── storage.py      # Data persistence layer
└── ui/             # UI layer (currently Streamlit)
    └── app.py
```

- **core/** must have ZERO UI dependencies
- **ui/** imports from core, never the reverse
- All AI logic lives in `core/extractor.py`

## Coding Standards

### Type Hints (Required)

All functions must have complete type annotations:

```python
def extract_card_data(raw_text: str) -> CardData:
    ...

def get_cards_by_issuer(issuer: str) -> list[Card]:
    ...
```

### Docstrings (Google Style)

```python
def parse_annual_fee(text: str) -> int | None:
    """Extract annual fee amount from card terms text.

    Args:
        text: Raw text containing card terms and conditions.

    Returns:
        Annual fee in dollars, or None if not found.

    Raises:
        ExtractionError: If text format is invalid.
    """
```

### Pydantic Models for Data

All structured data uses Pydantic for validation:

```python
from pydantic import BaseModel
from datetime import date

class Card(BaseModel):
    name: str
    issuer: str
    annual_fee: int
    signup_bonus: SignupBonus | None
    credits: list[Credit]
```

### Error Handling

- Use custom exceptions in `core/exceptions.py`
- Never let raw API errors bubble to UI
- Log errors with context

### Naming Conventions

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## AI Integration Guidelines

### Anthropic API Usage

- Model: `claude-sonnet-4-20250514` for extraction tasks
- Always use structured output (JSON mode) for parsing
- Keep prompts in separate constants for maintainability
- Include retry logic with exponential backoff

### Prompt Engineering

- Extraction prompts live in `core/prompts.py`
- Version prompts with comments
- Test prompts against edge cases before deploying

## Testing

- Unit tests in `tests/` mirror `src/` structure
- Mock external APIs in tests
- Minimum coverage: core extraction logic

## Environment

- Python 3.11+
- Dependencies in `requirements.txt`
- Secrets via environment variables (never commit)

## Change Verification

**Always verify changes compile/run before completing a task:**

```bash
# 1. Syntax check (catches typos, missing colons, etc.)
python -m py_compile src/core/module.py

# 2. Import check (catches missing dependencies, import errors)
# IMPORTANT: py_compile does NOT catch import errors!
python -c "import src.core.module"

# 3. Run the app to verify full functionality
streamlit run src/ui/app.py
```

**Verification Levels:**
| Check | Catches | Misses |
|-------|---------|--------|
| `py_compile` | Syntax errors | Missing imports, bad imports |
| `import module` | Import errors, missing deps | Runtime errors |
| Run app | Most issues | Edge cases |

**When adding new dependencies:**
1. Add to `requirements.txt`
2. **Always remind user to run `pip install -r requirements.txt`** - never assume they will do this
3. Verify with import check, not just syntax check

**Rules:**
- Never assume code works - verify it
- `py_compile` is NOT sufficient for files with new imports
- **Always use import checks (`python -c "import module"`) not just syntax checks for files with new imports**
- Test new features manually after implementation

## Git Workflow

- Commit messages: `type: description` (e.g., `feat: add SUB deadline parsing`)
- Types: `feat`, `fix`, `refactor`, `docs`, `test`
