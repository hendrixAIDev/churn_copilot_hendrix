"""Chase 5/24 rule calculation and application tracking."""

from datetime import date, timedelta
from src.core.models import Card


def calculate_five_twenty_four_status(cards: list[Card]) -> dict:
    """Calculate 5/24 status based on card portfolio.

    The 5/24 rule: Chase denies applications if you've opened 5+ personal credit cards
    from ANY issuer in the past 24 months.

    Args:
        cards: List of all cards in portfolio

    Returns:
        Dictionary with:
        - count: Current 5/24 count
        - status: "under" (can apply), "at" (risky), or "over" (will be denied)
        - cards_counted: List of cards that count toward 5/24
        - next_drop_off: Date when next card falls off (if any)
        - days_until_drop: Days until next card drops off
    """
    today = date.today()
    twenty_four_months_ago = today - timedelta(days=730)  # ~24 months

    # Cards that count toward 5/24:
    # - Personal cards (not business, with exceptions)
    # - Opened in last 24 months
    # - Not closed or opened_date is set
    cards_counted = []

    for card in cards:
        # Skip if no opened_date
        if not card.opened_date:
            continue

        # Skip if opened before 24 month window
        if card.opened_date <= twenty_four_months_ago:
            continue

        # Business cards generally don't count, EXCEPT:
        # - Capital One business cards DO count
        # - Discover business cards DO count
        # - TD Bank business cards DO count
        if card.is_business:
            issuer_lower = card.issuer.lower()
            if not any(x in issuer_lower for x in ["capital one", "discover", "td bank"]):
                continue  # Skip other business cards

        cards_counted.append(card)

    # Sort by opened_date
    cards_counted.sort(key=lambda c: c.opened_date)

    count = len(cards_counted)

    # Determine status
    if count < 5:
        status = "under"
    elif count == 5:
        status = "at"
    else:
        status = "over"

    # Calculate when next card drops off (first card to reach 24 months)
    next_drop_off = None
    days_until_drop = None

    if cards_counted:
        # Oldest card in the 24-month window
        oldest_card = cards_counted[0]
        # It drops off on the first day of the 25th month
        # If opened on 2024-01-15, drops off on 2026-02-01
        next_drop_off = date(
            oldest_card.opened_date.year + 2,
            oldest_card.opened_date.month + 1 if oldest_card.opened_date.month < 12 else 1,
            1
        )
        if oldest_card.opened_date.month == 12:
            next_drop_off = date(next_drop_off.year + 1, next_drop_off.month, 1)

        days_until_drop = (next_drop_off - today).days

        # If negative, it should have already dropped off (recalculate window)
        if days_until_drop < 0:
            next_drop_off = None
            days_until_drop = None

    return {
        "count": count,
        "status": status,
        "cards_counted": cards_counted,
        "next_drop_off": next_drop_off,
        "days_until_drop": days_until_drop,
    }


def get_five_twenty_four_timeline(cards: list[Card]) -> list[dict]:
    """Get a timeline of when cards will drop off 5/24 count.

    Args:
        cards: List of all cards in portfolio

    Returns:
        List of dicts with:
        - card: Card object
        - drop_off_date: Date when it drops off
        - days_until: Days until drop off
    """
    today = date.today()
    twenty_four_months_ago = today - timedelta(days=730)

    timeline = []

    for card in cards:
        if not card.opened_date:
            continue

        # Skip cards that already dropped off
        if card.opened_date <= twenty_four_months_ago:
            continue

        # Skip business cards (except Cap1, Discover, TD)
        if card.is_business:
            issuer_lower = card.issuer.lower()
            if not any(x in issuer_lower for x in ["capital one", "discover", "td bank"]):
                continue

        # Calculate drop off date (first day of 25th month)
        drop_off = date(
            card.opened_date.year + 2,
            card.opened_date.month + 1 if card.opened_date.month < 12 else 1,
            1
        )
        if card.opened_date.month == 12:
            drop_off = date(drop_off.year + 1, drop_off.month, 1)

        days_until = (drop_off - today).days

        timeline.append({
            "card": card,
            "drop_off_date": drop_off,
            "days_until": days_until,
        })

    # Sort by drop off date
    timeline.sort(key=lambda x: x["drop_off_date"])

    return timeline
