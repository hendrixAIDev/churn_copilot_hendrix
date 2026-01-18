"""Unit tests for 5/24 rule calculation."""

import pytest
from datetime import date, timedelta
from src.core.models import Card
from src.core.five_twenty_four import calculate_five_twenty_four_status, get_five_twenty_four_timeline


def test_under_five_twenty_four():
    """Test user with fewer than 5 cards."""
    today = date.today()
    cards = [
        Card(
            id="1",
            name="Test Card 1",
            issuer="Chase",
            opened_date=today - timedelta(days=90),
            is_business=False,
        ),
        Card(
            id="2",
            name="Test Card 2",
            issuer="Amex",
            opened_date=today - timedelta(days=180),
            is_business=False,
        ),
    ]

    status = calculate_five_twenty_four_status(cards)
    assert status["count"] == 2
    assert status["status"] == "under"


def test_at_five_twenty_four():
    """Test user exactly at 5/24."""
    today = date.today()
    cards = [
        Card(id=str(i), name=f"Card {i}", issuer="Chase", opened_date=today - timedelta(days=i * 100), is_business=False)
        for i in range(1, 6)
    ]

    status = calculate_five_twenty_four_status(cards)
    assert status["count"] == 5
    assert status["status"] == "at"


def test_over_five_twenty_four():
    """Test user over 5/24."""
    today = date.today()
    cards = [
        Card(id=str(i), name=f"Card {i}", issuer="Chase", opened_date=today - timedelta(days=i * 50), is_business=False)
        for i in range(1, 8)
    ]

    status = calculate_five_twenty_four_status(cards)
    assert status["count"] == 7
    assert status["status"] == "over"


def test_business_cards_excluded():
    """Test that most business cards don't count."""
    today = date.today()
    cards = [
        Card(id="1", name="Personal Card", issuer="Chase", opened_date=today - timedelta(days=90), is_business=False),
        Card(id="2", name="Business Card", issuer="Chase", opened_date=today - timedelta(days=60), is_business=True),
        Card(id="3", name="Business Card 2", issuer="Amex", opened_date=today - timedelta(days=30), is_business=True),
    ]

    status = calculate_five_twenty_four_status(cards)
    assert status["count"] == 1  # Only personal card counts


def test_capital_one_business_counts():
    """Test that Capital One business cards DO count."""
    today = date.today()
    cards = [
        Card(id="1", name="Personal Card", issuer="Chase", opened_date=today - timedelta(days=90), is_business=False),
        Card(id="2", name="Cap1 Business", issuer="Capital One", opened_date=today - timedelta(days=60), is_business=True),
    ]

    status = calculate_five_twenty_four_status(cards)
    assert status["count"] == 2  # Both count


def test_old_cards_excluded():
    """Test that cards over 24 months old don't count."""
    today = date.today()
    cards = [
        Card(id="1", name="Recent Card", issuer="Chase", opened_date=today - timedelta(days=90), is_business=False),
        Card(id="2", name="Old Card", issuer="Amex", opened_date=today - timedelta(days=800), is_business=False),
    ]

    status = calculate_five_twenty_four_status(cards)
    assert status["count"] == 1  # Only recent card counts


def test_timeline_ordering():
    """Test that timeline is ordered by drop-off date."""
    today = date.today()
    cards = [
        Card(id="1", name="Newest", issuer="Chase", opened_date=today - timedelta(days=90), is_business=False),
        Card(id="2", name="Middle", issuer="Amex", opened_date=today - timedelta(days=365), is_business=False),
        Card(id="3", name="Oldest", issuer="Citi", opened_date=today - timedelta(days=600), is_business=False),
    ]

    timeline = get_five_twenty_four_timeline(cards)

    assert len(timeline) == 3
    # Oldest card should drop off first
    assert timeline[0]["card"].name == "Oldest"
    assert timeline[1]["card"].name == "Middle"
    assert timeline[2]["card"].name == "Newest"


def test_no_opened_date():
    """Test that cards without opened_date are excluded."""
    today = date.today()
    cards = [
        Card(id="1", name="With Date", issuer="Chase", opened_date=today - timedelta(days=90), is_business=False),
        Card(id="2", name="No Date", issuer="Amex", is_business=False),
    ]

    status = calculate_five_twenty_four_status(cards)
    assert status["count"] == 1  # Only card with date counts
