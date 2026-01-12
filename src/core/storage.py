"""Data persistence layer for ChurnPilot."""

import json
import uuid
from datetime import date
from pathlib import Path

from .exceptions import StorageError
from .models import Card, CardData


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
            raise StorageError(f"Failed to load cards: {e}")

    def _save_cards(self, cards: list[dict]) -> None:
        """Save card data to JSON file."""
        try:
            self.cards_file.write_text(
                json.dumps(cards, indent=2, default=str)
            )
        except IOError as e:
            raise StorageError(f"Failed to save cards: {e}")

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
        card = Card(
            id=str(uuid.uuid4()),
            name=card_data.name,
            issuer=card_data.issuer,
            annual_fee=card_data.annual_fee,
            signup_bonus=card_data.signup_bonus,
            credits=card_data.credits,
            opened_date=opened_date,
            raw_text=raw_text,
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

        for i, c in enumerate(raw_cards):
            if c.get("id") == card_id:
                raw_cards[i].update(updates)
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
