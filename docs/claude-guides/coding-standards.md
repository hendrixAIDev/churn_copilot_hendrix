# Coding Standards

## Type Hints (Required)

All functions must have complete type annotations:

```python
def extract_card_data(raw_text: str) -> CardData:
    ...

def get_cards_by_issuer(issuer: str) -> list[Card]:
    ...
```

## Docstrings (Google Style)

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

## Pydantic Models for Data

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

## Error Handling

- Use custom exceptions in `core/exceptions.py`
- Never let raw API errors bubble to UI
- Log errors with context

## Naming Conventions

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## Git Workflow

- Commit messages: `type: description` (e.g., `feat: add SUB deadline parsing`)
- Types: `feat`, `fix`, `refactor`, `docs`, `test`
