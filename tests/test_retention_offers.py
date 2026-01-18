"""Unit tests for retention offer tracking."""

import pytest
from datetime import date
from src.core.models import Card, RetentionOffer


def test_retention_offer_creation():
    """Test creating a retention offer."""
    offer = RetentionOffer(
        date_called=date(2026, 1, 15),
        offer_details="20,000 points after $2,000 spend in 3 months",
        accepted=True,
        notes="Called before AF posted"
    )

    assert offer.date_called == date(2026, 1, 15)
    assert offer.accepted is True
    assert offer.notes == "Called before AF posted"


def test_card_with_retention_offers():
    """Test card with retention offers."""
    card = Card(
        id="test",
        name="Amex Platinum",
        issuer="American Express",
        retention_offers=[
            RetentionOffer(
                date_called=date(2025, 1, 1),
                offer_details="No offer",
                accepted=False,
            ),
            RetentionOffer(
                date_called=date(2026, 1, 1),
                offer_details="20,000 points",
                accepted=True,
            ),
        ]
    )

    assert len(card.retention_offers) == 2
    assert card.retention_offers[0].accepted is False
    assert card.retention_offers[1].accepted is True


def test_card_business_flag():
    """Test business card flag."""
    business_card = Card(
        id="test",
        name="Chase Ink",
        issuer="Chase",
        is_business=True,
    )

    personal_card = Card(
        id="test2",
        name="Chase Sapphire",
        issuer="Chase",
        is_business=False,
    )

    assert business_card.is_business is True
    assert personal_card.is_business is False


def test_card_closed_date():
    """Test closed date tracking."""
    card = Card(
        id="test",
        name="Old Card",
        issuer="Chase",
        opened_date=date(2020, 1, 1),
        closed_date=date(2022, 1, 1),
    )

    assert card.closed_date == date(2022, 1, 1)
    assert card.opened_date == date(2020, 1, 1)
