"""Data persistence layer for ChurnPilot."""

import json
import uuid
from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel

from .exceptions import StorageError
from .models import Card, CardData, SignupBonus
from .library import CardTemplate
from .normalize import normalize_issuer, match_to_library_template


def _serialize_for_json(obj):
    """Recursively convert Pydantic models and other types for JSON serialization."""
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    elif isinstance(obj, (date, datetime)):
        return obj.isoformat()
    else:
        return obj


class CardStorage:
    """JSON file-based storage for card data."""

    def __init__(self, data_dir: str | Path = "data"):
        """Initialize storage with data directory.

        Args:
            data_dir: Directory to store JSON data files.
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cards_file = self.data_dir / "cards.json"
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create cards file if it doesn't exist."""
        if not self.cards_file.exists():
            self.cards_file.write_text("[]")

    def _load_cards(self) -> list[dict]:
        """Load raw card data from JSON file."""
        try:
            content = self.cards_file.read_text()
            return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            import logging
            logging.error(f"Failed to load cards: {e}")
            raise StorageError("Unable to load your saved cards")

    def _save_cards(self, cards: list[dict]) -> None:
        """Save card data to JSON file."""
        try:
            self.cards_file.write_text(
                json.dumps(cards, indent=2, default=str)
            )
        except IOError as e:
            import logging
            logging.error(f"Failed to save cards: {e}")
            raise StorageError("Unable to save your cards")

    def get_all_cards(self) -> list[Card]:
        """Retrieve all stored cards.

        Returns:
            List of Card objects.
        """
        raw_cards = self._load_cards()
        return [Card.model_validate(c) for c in raw_cards]

    def get_card(self, card_id: str) -> Card | None:
        """Retrieve a single card by ID.

        Args:
            card_id: Unique card identifier.

        Returns:
            Card object if found, None otherwise.
        """
        cards = self.get_all_cards()
        for card in cards:
            if card.id == card_id:
                return card
        return None

    def add_card(
        self,
        card_data: CardData,
        opened_date: date | None = None,
        raw_text: str | None = None,
    ) -> Card:
        """Add a new card from extracted data.

        Args:
            card_data: Extracted card data from AI.
            opened_date: When the card was opened.
            raw_text: Original text used for extraction.

        Returns:
            The created Card object with generated ID.
        """
        # Normalize issuer
        normalized_issuer = normalize_issuer(card_data.issuer)

        # Try to match to library template
        template_id = match_to_library_template(card_data.name, normalized_issuer)

        card = Card(
            id=str(uuid.uuid4()),
            name=card_data.name,
            issuer=normalized_issuer,
            annual_fee=card_data.annual_fee,
            signup_bonus=card_data.signup_bonus,
            credits=card_data.credits,
            opened_date=opened_date,
            raw_text=raw_text,
            template_id=template_id,
            created_at=datetime.now(),
        )

        raw_cards = self._load_cards()
        raw_cards.append(card.model_dump())
        self._save_cards(raw_cards)

        return card

    def add_card_from_template(
        self,
        template: CardTemplate,
        nickname: str | None = None,
        opened_date: date | None = None,
        signup_bonus: SignupBonus | None = None,
    ) -> Card:
        """Add a new card from a library template.

        Args:
            template: Card template from the library.
            nickname: User-defined nickname for the card.
            opened_date: When the card was opened.
            signup_bonus: Optional signup bonus details.

        Returns:
            The created Card object with generated ID.
        """
        card = Card(
            id=str(uuid.uuid4()),
            name=template.name,
            nickname=nickname,
            issuer=template.issuer,
            annual_fee=template.annual_fee,
            signup_bonus=signup_bonus,
            credits=template.credits,
            opened_date=opened_date,
            template_id=template.id,
            created_at=datetime.now(),
        )

        raw_cards = self._load_cards()
        raw_cards.append(card.model_dump())
        self._save_cards(raw_cards)

        return card

    def update_card(self, card_id: str, updates: dict) -> Card | None:
        """Update an existing card.

        Args:
            card_id: Card to update.
            updates: Dictionary of fields to update.

        Returns:
            Updated Card object, or None if not found.
        """
        raw_cards = self._load_cards()

        # Serialize any Pydantic models in the updates to dicts
        serialized_updates = _serialize_for_json(updates)

        for i, c in enumerate(raw_cards):
            if c.get("id") == card_id:
                raw_cards[i].update(serialized_updates)
                self._save_cards(raw_cards)
                return Card.model_validate(raw_cards[i])

        return None

    def delete_card(self, card_id: str) -> bool:
        """Delete a card by ID.

        Args:
            card_id: Card to delete.

        Returns:
            True if deleted, False if not found.
        """
        raw_cards = self._load_cards()
        original_len = len(raw_cards)

        raw_cards = [c for c in raw_cards if c.get("id") != card_id]

        if len(raw_cards) < original_len:
            self._save_cards(raw_cards)
            return True

        return False
