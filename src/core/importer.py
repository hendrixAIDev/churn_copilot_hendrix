"""Flexible spreadsheet importer using Claude API."""

import anthropic
import os
import re
from datetime import date, datetime, timedelta
from typing import Optional
from pydantic import BaseModel

from .models import Card, SignupBonus, Credit, CreditUsage
from .storage import CardStorage
from .library import get_all_templates
from .normalize import normalize_issuer, match_to_library_template
from .periods import mark_credit_used


class ParsedCard(BaseModel):
    """Intermediate representation of a parsed card."""
    card_name: str
    status: Optional[str] = None
    annual_fee: float = 0.0
    opened_date: Optional[date] = None
    sub_reward: Optional[str] = None
    sub_spend_requirement: Optional[float] = None
    sub_time_period_days: Optional[int] = None
    sub_deadline: Optional[date] = None
    sub_achieved: Optional[bool] = None  # Allow None, will convert to False
    benefits: list[dict] = []  # {name, amount, frequency, is_used}
    notes: Optional[str] = None

    def normalize(self) -> "ParsedCard":
        """Normalize and clean up parsed data."""
        # Convert None to False for sub_achieved
        if self.sub_achieved is None:
            self.sub_achieved = False

        # Ensure annual_fee is non-negative
        if self.annual_fee < 0:
            self.annual_fee = 0.0

        # Clean up card name
        self.card_name = self.card_name.strip()

        return self


class SpreadsheetImporter:
    """Import cards from spreadsheets using Claude API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize importer with Anthropic API key.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.storage = CardStorage()

    def parse_spreadsheet(self, csv_content: str, skip_closed: bool = True) -> tuple[list[ParsedCard], list[str]]:
        """Parse spreadsheet content using Claude API.

        Args:
            csv_content: Raw CSV/TSV content of the spreadsheet
            skip_closed: Whether to skip cards marked as closed

        Returns:
            Tuple of (successfully_parsed_cards, error_messages)
        """
        # Get available templates for matching
        templates = get_all_templates()
        template_names = [f"{t.issuer} {t.name}" for t in templates]

        prompt = f"""You are parsing a credit card tracking spreadsheet into structured data.

The spreadsheet may be in any format, any language (English, Chinese, etc.), with any column names.

Your task: Extract card information and output JSON for each card.

Available card templates in our library:
{chr(10).join(f"- {name}" for name in template_names[:20])}
(and {len(template_names) - 20} more...)

For each card, extract:
1. **card_name**: The card name (normalize to match our templates if possible)
2. **status**: Card status (e.g., "Long-term", "Closed", "Active", etc.)
3. **annual_fee**: Annual fee as a number (0 if free)
4. **opened_date**: When card was opened (YYYY-MM-DD format)
5. **sub_reward**: Signup bonus reward text (e.g., "80,000 points", "$500 cash")
6. **sub_spend_requirement**: Dollar amount to spend for SUB
7. **sub_time_period_days**: Days to complete SUB (3 months = 90, 6 months = 180)
8. **sub_deadline**: Actual deadline date if you can calculate it
9. **sub_achieved**: true if SUB is already earned/completed
10. **benefits**: Array of benefits with:
    - name: Benefit name
    - amount: Dollar amount
    - frequency: "monthly", "quarterly", "semi-annually", "annual"
    - is_used: true if marked as used/completed for current period
11. **notes**: Any important notes

**Benefit parsing rules:**
- Look for TODO/pending sections (unused benefits)
- Look for Waiting/completed sections (used benefits)
- Parse periods: Q1-Q4 (quarterly), H1-H2 (semi-annual), CY (calendar year = annual), monthly
- Extract dollar amounts like "$50", "$200"

Skip cards marked as "Closed" if they're clearly no longer active.

Output ONLY a JSON array of cards. No markdown, no explanations.

Spreadsheet content:
```
{csv_content}
```

Output format:
```json
[
  {{
    "card_name": "Chase Sapphire Preferred",
    "status": "Long-term",
    "annual_fee": 95,
    "opened_date": "2023-03-18",
    "sub_reward": "60k points",
    "sub_spend_requirement": 4000,
    "sub_time_period_days": 90,
    "sub_achieved": true,
    "benefits": [
      {{"name": "Hotel Credit", "amount": 50, "frequency": "annual", "is_used": false}}
    ],
    "notes": "..."
  }}
]
```"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Try to extract JSON array
        json_match = re.search(r'\[\s*\{.*\}\s*\]', response_text, re.DOTALL)
        if not json_match:
            raise ValueError("Failed to parse response as JSON array")

        import json
        cards_data = json.loads(json_match.group(0))

        # Convert to ParsedCard objects (best-effort)
        parsed_cards = []
        errors = []

        for i, card_data in enumerate(cards_data, 1):
            try:
                # Skip closed cards if requested
                if skip_closed and card_data.get("status", "").lower() == "closed":
                    continue

                # Parse dates
                if card_data.get("opened_date"):
                    try:
                        card_data["opened_date"] = datetime.strptime(
                            card_data["opened_date"], "%Y-%m-%d"
                        ).date()
                    except:
                        card_data["opened_date"] = None

                if card_data.get("sub_deadline"):
                    try:
                        card_data["sub_deadline"] = datetime.strptime(
                            card_data["sub_deadline"], "%Y-%m-%d"
                        ).date()
                    except:
                        card_data["sub_deadline"] = None

                # Create and normalize the parsed card
                parsed_card = ParsedCard(**card_data).normalize()
                parsed_cards.append(parsed_card)

            except Exception as e:
                # Collect error but continue processing other cards
                card_name = card_data.get("card_name", f"Card #{i}")
                errors.append(f"{card_name}: {str(e)}")

        return parsed_cards, errors

    def import_cards(
        self,
        parsed_cards: list[ParsedCard],
        auto_match_templates: bool = True
    ) -> list[Card]:
        """Import parsed cards into the system.

        Args:
            parsed_cards: List of ParsedCard objects to import
            auto_match_templates: Whether to automatically match to library templates

        Returns:
            List of imported Card objects
        """
        imported_cards = []

        for parsed in parsed_cards:
            # Try to match to a template
            template_id = None
            if auto_match_templates:
                normalized_issuer = normalize_issuer(parsed.card_name)
                template_id = match_to_library_template(parsed.card_name, normalized_issuer)

            # Build signup bonus if present
            signup_bonus = None
            if parsed.sub_reward:
                signup_bonus = SignupBonus(
                    points_or_cash=parsed.sub_reward,
                    spend_requirement=parsed.sub_spend_requirement or 0,
                    time_period_days=parsed.sub_time_period_days or 90,
                    deadline=parsed.sub_deadline
                )

            # Build credits from benefits
            credits = []
            credit_usage = {}

            for benefit in parsed.benefits:
                credit = Credit(
                    name=benefit["name"],
                    amount=benefit["amount"],
                    frequency=benefit["frequency"]
                )
                credits.append(credit)

                # Mark as used if indicated
                if benefit.get("is_used", False):
                    credit_usage[benefit["name"]] = mark_credit_used(
                        benefit["name"],
                        benefit["frequency"],
                        {},
                        date.today()
                    )[benefit["name"]]

            # Create card
            from .models import Card as CardModel
            import uuid

            card = CardModel(
                id=str(uuid.uuid4()),
                name=parsed.card_name,
                issuer=normalize_issuer(parsed.card_name),
                annual_fee=parsed.annual_fee,
                signup_bonus=signup_bonus,
                credits=credits,
                opened_date=parsed.opened_date,
                template_id=template_id,
                created_at=datetime.now(),
                sub_achieved=parsed.sub_achieved,
                credit_usage=credit_usage,
                notes=parsed.notes
            )

            # Save to storage
            raw_cards = self.storage._load_cards()
            raw_cards.append(card.model_dump())
            self.storage._save_cards(raw_cards)

            imported_cards.append(card)

        return imported_cards


def import_from_csv(csv_content: str, skip_closed: bool = True) -> tuple[list[ParsedCard], list[str]]:
    """Import cards from CSV content (best-effort).

    Args:
        csv_content: Raw CSV/TSV content
        skip_closed: Whether to skip closed cards

    Returns:
        Tuple of (parsed_cards, errors)
        - parsed_cards: Successfully parsed cards (may be partial)
        - errors: List of error messages for failed cards
    """
    try:
        importer = SpreadsheetImporter()
        parsed_cards, parse_errors = importer.parse_spreadsheet(csv_content, skip_closed=skip_closed)
        return parsed_cards, parse_errors
    except Exception as e:
        return [], [f"Critical error: {str(e)}"]
