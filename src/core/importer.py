"""Flexible spreadsheet importer using AI (Gemini default, Claude fallback)."""

import os
import re
from datetime import date, datetime, timedelta
from typing import Optional
from pydantic import BaseModel

from .models import Card, SignupBonus, Credit, CreditUsage
from .storage import CardStorage
from .library import get_all_templates, get_template
from .normalize import normalize_issuer, match_to_library_template
from .periods import mark_credit_used

# AI provider selection (same as pipeline.py)
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class ParsedCard(BaseModel):
    """Intermediate representation of a parsed card."""
    card_name: str
    nickname: Optional[str] = None
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

    def calculate_deadline(self) -> Optional[date]:
        """Calculate SUB deadline from opened_date + time_period_days.

        Returns:
            Calculated deadline date, or None if insufficient data.
        """
        if self.opened_date and self.sub_time_period_days and not self.sub_deadline:
            return self.opened_date + timedelta(days=self.sub_time_period_days)
        return self.sub_deadline

    def get_days_remaining(self, reference_date: Optional[date] = None) -> Optional[int]:
        """Calculate days remaining until SUB deadline.

        Args:
            reference_date: Date to calculate from (defaults to today).

        Returns:
            Number of days remaining, or None if no deadline available.
        """
        deadline = self.calculate_deadline()
        if not deadline:
            return None

        ref = reference_date or date.today()
        delta = deadline - ref
        return delta.days

    def calculate_annual_fee_date(self) -> Optional[date]:
        """Calculate next annual fee date from opened_date.

        Returns:
            Next annual fee date (1 year from opened_date), or None if no opened_date.
        """
        if self.opened_date:
            # Annual fee typically posts 1 year from account opening
            return date(self.opened_date.year + 1, self.opened_date.month, self.opened_date.day)
        return None

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

        # Auto-calculate SUB deadline if not provided
        if not self.sub_deadline and self.opened_date and self.sub_time_period_days:
            self.sub_deadline = self.calculate_deadline()

        return self


class SpreadsheetImporter:
    """Import cards from spreadsheets using AI (Gemini default, Claude fallback)."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize importer with API key.

        Args:
            api_key: API key (Gemini or Claude depending on AI_PROVIDER).
        """
        self.provider = AI_PROVIDER.lower()
        
        if self.provider == "gemini":
            # Try Gemini first
            self.gemini_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not self.gemini_key:
                try:
                    import streamlit as st
                    self.gemini_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
                except:
                    pass
            
            # Also get Claude key for fallback
            self.claude_key = os.getenv("ANTHROPIC_API_KEY")
            if not self.claude_key:
                try:
                    import streamlit as st
                    self.claude_key = st.secrets.get("ANTHROPIC_API_KEY")
                except:
                    pass
            
            if not self.gemini_key and not self.claude_key:
                raise ValueError("Neither GEMINI_API_KEY nor ANTHROPIC_API_KEY found")
        else:
            # Claude mode
            self.claude_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.claude_key:
                try:
                    import streamlit as st
                    self.claude_key = st.secrets.get("ANTHROPIC_API_KEY")
                except:
                    pass
            
            if not self.claude_key:
                raise ValueError("ANTHROPIC_API_KEY not found")
            
            self.gemini_key = None
        
        self.storage = CardStorage()

    def _call_ai(self, prompt: str) -> str:
        """Call AI provider and return response text.
        
        Uses Gemini by default, falls back to Claude on failure.
        
        Args:
            prompt: The prompt to send to the AI.
            
        Returns:
            Response text from the AI.
        """
        if self.provider == "gemini" and self.gemini_key:
            try:
                return self._call_gemini(prompt)
            except Exception as e:
                import logging
                logging.warning(f"Gemini failed: {e}, falling back to Claude")
                if self.claude_key:
                    return self._call_claude(prompt)
                raise
        else:
            return self._call_claude(prompt)
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API."""
        from google import genai
        client = genai.Client(api_key=self.gemini_key)
        
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text
    
    def _call_claude(self, prompt: str) -> str:
        """Call Claude API."""
        import anthropic
        client = anthropic.Anthropic(api_key=self.claude_key)
        
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def parse_spreadsheet(self, csv_content: str, skip_closed: bool = True) -> tuple[list[ParsedCard], list[str]]:
        """Parse spreadsheet content using AI (Gemini default, Claude fallback).

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
2. **nickname**: User's nickname for the card (e.g., "P2's Card", "My Card", etc.) - optional
3. **status**: Card status (e.g., "Long-term", "Closed", "Active", etc.)
4. **annual_fee**: Annual fee as a number (0 if free)
5. **opened_date**: When card was opened (YYYY-MM-DD format)
6. **sub_reward**: Signup bonus reward text (e.g., "80,000 points", "$500 cash")
7. **sub_spend_requirement**: Dollar amount to spend for SUB
8. **sub_time_period_days**: Days to complete SUB (3 months = 90, 6 months = 180)
9. **sub_deadline**: Actual deadline date if you can calculate it
10. **sub_achieved**: true if SUB is already earned/completed
11. **benefits**: Array of benefits with:
    - name: Benefit name
    - amount: Dollar amount
    - frequency: "monthly", "quarterly", "semi-annually", "annual"
    - is_used: true if marked as used/completed for current period
12. **notes**: Any important notes

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
    "nickname": "P2's Card",
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

        # Call AI provider (Gemini default, Claude fallback)
        response_text = self._call_ai(prompt)

        # Continue with existing parsing logic below

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

            # First, add credits from parsed benefits
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

            # Enrich with library template credits (if matched)
            if template_id:
                template = get_template(template_id)
                if template:
                    # Get existing credit names (case-insensitive)
                    existing_names = {c.name.lower() for c in credits}

                    # Add missing credits from template
                    credits_added = 0
                    for template_credit in template.credits:
                        if template_credit.name.lower() not in existing_names:
                            credits.append(template_credit.model_copy())
                            credits_added += 1

                    # Log enrichment
                    if credits_added > 0:
                        print(f"[Import Enrichment] {parsed.card_name}: Added {credits_added} credits from library")

            # Create card
            from .models import Card as CardModel
            import uuid

            # Calculate annual fee date if we have opened_date
            annual_fee_date = parsed.calculate_annual_fee_date()

            card = CardModel(
                id=str(uuid.uuid4()),
                name=parsed.card_name,
                nickname=parsed.nickname,
                issuer=normalize_issuer(parsed.card_name),
                annual_fee=parsed.annual_fee,
                signup_bonus=signup_bonus,
                credits=credits,
                opened_date=parsed.opened_date,
                annual_fee_date=annual_fee_date,
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
