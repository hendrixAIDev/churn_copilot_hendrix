"""Database storage for ChurnPilot.

Provides the same interface as WebStorage but backed by PostgreSQL.
All operations are scoped to a specific user_id.
"""

from datetime import date, datetime
from uuid import UUID
import uuid as uuid_module

from .database import get_cursor
from .models import (
    Card, CardData, SignupBonus, Credit,
    CreditUsage, RetentionOffer, ProductChange
)
from .preferences import UserPreferences
from .library import CardTemplate
from .normalize import normalize_issuer, match_to_library_template


class DatabaseStorage:
    """PostgreSQL-backed storage for a single user."""

    def __init__(self, user_id: UUID):
        """Initialize storage for a user.

        Args:
            user_id: The user's UUID (all operations scoped to this user).
        """
        self.user_id = user_id

    # ==================== CARDS ====================

    def get_all_cards(self) -> list[Card]:
        """Get all cards for the user.

        Returns:
            List of Card objects.
        """
        with get_cursor(commit=False) as cursor:
            # Get cards
            cursor.execute(
                """
                SELECT * FROM cards WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (str(self.user_id),)
            )
            card_rows = cursor.fetchall()

            cards = []
            for row in card_rows:
                card_id = row["id"]

                # Get signup bonus
                cursor.execute(
                    "SELECT * FROM signup_bonuses WHERE card_id = %s",
                    (str(card_id),)
                )
                sub_row = cursor.fetchone()
                signup_bonus = None
                sub_progress = None
                sub_achieved = False
                if sub_row:
                    signup_bonus = SignupBonus(
                        points_or_cash=sub_row["points_or_cash"],
                        spend_requirement=sub_row["spend_requirement"],
                        time_period_days=sub_row["time_period_days"],
                        deadline=sub_row["deadline"],
                    )
                    sub_progress = sub_row["spend_progress"]
                    sub_achieved = sub_row["achieved"]

                # Get credits
                cursor.execute(
                    "SELECT * FROM card_credits WHERE card_id = %s",
                    (str(card_id),)
                )
                credit_rows = cursor.fetchall()
                credits = [
                    Credit(
                        name=r["name"],
                        amount=r["amount"],
                        frequency=r["frequency"],
                        notes=r["notes"],
                    )
                    for r in credit_rows
                ]

                # Get credit usage
                cursor.execute(
                    "SELECT * FROM credit_usage WHERE card_id = %s",
                    (str(card_id),)
                )
                usage_rows = cursor.fetchall()
                credit_usage = {
                    r["credit_name"]: CreditUsage(
                        last_used_period=r["last_used_period"],
                        reminder_snoozed_until=r["reminder_snoozed_until"],
                    )
                    for r in usage_rows
                }

                # Get retention offers
                cursor.execute(
                    "SELECT * FROM retention_offers WHERE card_id = %s ORDER BY date_called DESC",
                    (str(card_id),)
                )
                retention_rows = cursor.fetchall()
                retention_offers = [
                    RetentionOffer(
                        date_called=r["date_called"],
                        offer_details=r["offer_details"],
                        accepted=r["accepted"],
                        notes=r["notes"],
                    )
                    for r in retention_rows
                ]

                # Get product changes
                cursor.execute(
                    "SELECT * FROM product_changes WHERE card_id = %s ORDER BY date_changed DESC",
                    (str(card_id),)
                )
                change_rows = cursor.fetchall()
                product_changes = [
                    ProductChange(
                        date_changed=r["date_changed"],
                        from_product=r["from_product"],
                        to_product=r["to_product"],
                        reason=r["reason"],
                        notes=r["notes"],
                    )
                    for r in change_rows
                ]

                # Build card
                card = Card(
                    id=str(card_id),
                    name=row["name"],
                    nickname=row["nickname"],
                    issuer=row["issuer"],
                    annual_fee=row["annual_fee"],
                    signup_bonus=signup_bonus,
                    sub_spend_progress=sub_progress,
                    sub_achieved=sub_achieved,
                    credits=credits,
                    opened_date=row["opened_date"],
                    annual_fee_date=row["annual_fee_date"],
                    closed_date=row["closed_date"],
                    is_business=row["is_business"],
                    notes=row["notes"],
                    raw_text=row["raw_text"],
                    template_id=row["template_id"],
                    created_at=row["created_at"],
                    credit_usage=credit_usage,
                    benefits_reminder_snoozed_until=row["benefits_reminder_snoozed_until"],
                    retention_offers=retention_offers,
                    product_change_history=product_changes,
                )
                cards.append(card)

            return cards

    def get_card(self, card_id: str) -> Card | None:
        """Get a single card by ID.

        Args:
            card_id: The card's UUID string.

        Returns:
            Card if found, None otherwise.
        """
        cards = self.get_all_cards()
        for card in cards:
            if card.id == card_id:
                return card
        return None

    def save_card(self, card: Card) -> Card:
        """Save a card (insert or update).

        Args:
            card: Card to save.

        Returns:
            Saved card.
        """
        with get_cursor() as cursor:
            # Check if card exists
            cursor.execute(
                "SELECT id FROM cards WHERE id = %s AND user_id = %s",
                (card.id, str(self.user_id))
            )
            exists = cursor.fetchone() is not None

            if exists:
                # Update
                cursor.execute(
                    """
                    UPDATE cards SET
                        name = %s, nickname = %s, issuer = %s, annual_fee = %s,
                        opened_date = %s, annual_fee_date = %s, closed_date = %s,
                        is_business = %s, notes = %s, raw_text = %s, template_id = %s,
                        benefits_reminder_snoozed_until = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    """,
                    (
                        card.name, card.nickname, card.issuer, card.annual_fee,
                        card.opened_date, card.annual_fee_date, card.closed_date,
                        card.is_business, card.notes, card.raw_text, card.template_id,
                        card.benefits_reminder_snoozed_until, card.id, str(self.user_id)
                    )
                )
            else:
                # Insert
                cursor.execute(
                    """
                    INSERT INTO cards (
                        id, user_id, name, nickname, issuer, annual_fee,
                        opened_date, annual_fee_date, closed_date, is_business,
                        notes, raw_text, template_id, benefits_reminder_snoozed_until, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        card.id, str(self.user_id), card.name, card.nickname,
                        card.issuer, card.annual_fee, card.opened_date,
                        card.annual_fee_date, card.closed_date, card.is_business,
                        card.notes, card.raw_text, card.template_id,
                        card.benefits_reminder_snoozed_until,
                        card.created_at or datetime.now()
                    )
                )

            # Save signup bonus
            cursor.execute("DELETE FROM signup_bonuses WHERE card_id = %s", (card.id,))
            if card.signup_bonus:
                cursor.execute(
                    """
                    INSERT INTO signup_bonuses (
                        card_id, points_or_cash, spend_requirement, time_period_days,
                        deadline, spend_progress, achieved
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        card.id, card.signup_bonus.points_or_cash,
                        card.signup_bonus.spend_requirement,
                        card.signup_bonus.time_period_days,
                        card.signup_bonus.deadline,
                        card.sub_spend_progress or 0,
                        card.sub_achieved or False
                    )
                )

            # Save credits
            cursor.execute("DELETE FROM card_credits WHERE card_id = %s", (card.id,))
            for credit in card.credits:
                cursor.execute(
                    """
                    INSERT INTO card_credits (card_id, name, amount, frequency, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (card.id, credit.name, credit.amount, credit.frequency, credit.notes)
                )

            # Save credit usage
            cursor.execute("DELETE FROM credit_usage WHERE card_id = %s", (card.id,))
            for credit_name, usage in card.credit_usage.items():
                cursor.execute(
                    """
                    INSERT INTO credit_usage (card_id, credit_name, last_used_period, reminder_snoozed_until)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (card.id, credit_name, usage.last_used_period, usage.reminder_snoozed_until)
                )

            # Save retention offers
            cursor.execute("DELETE FROM retention_offers WHERE card_id = %s", (card.id,))
            for offer in card.retention_offers:
                cursor.execute(
                    """
                    INSERT INTO retention_offers (card_id, date_called, offer_details, accepted, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (card.id, offer.date_called, offer.offer_details, offer.accepted, offer.notes)
                )

            # Save product changes
            cursor.execute("DELETE FROM product_changes WHERE card_id = %s", (card.id,))
            for change in card.product_change_history:
                cursor.execute(
                    """
                    INSERT INTO product_changes (card_id, date_changed, from_product, to_product, reason, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (card.id, change.date_changed, change.from_product, change.to_product, change.reason, change.notes)
                )

        return card

    def add_card(
        self,
        card_data: CardData,
        opened_date: date | None = None,
        raw_text: str | None = None,
    ) -> Card:
        """Add a card from extracted data.

        Args:
            card_data: Extracted card data.
            opened_date: When card was opened.
            raw_text: Original text used for extraction.

        Returns:
            Created Card.
        """
        card = Card(
            id=str(uuid_module.uuid4()),
            name=card_data.name,
            issuer=normalize_issuer(card_data.issuer),
            annual_fee=card_data.annual_fee,
            signup_bonus=card_data.signup_bonus,
            credits=card_data.credits,
            opened_date=opened_date,
            raw_text=raw_text,
            template_id=match_to_library_template(
                card_data.name,
                normalize_issuer(card_data.issuer)
            ),
            created_at=datetime.now(),
        )
        return self.save_card(card)

    def add_card_from_template(
        self,
        template: CardTemplate,
        nickname: str | None = None,
        opened_date: date | None = None,
        signup_bonus: SignupBonus | None = None,
    ) -> Card:
        """Add a card from a library template.

        Args:
            template: Library template.
            nickname: User nickname for card.
            opened_date: When card was opened.
            signup_bonus: SUB details.

        Returns:
            Created Card.
        """
        card = Card(
            id=str(uuid_module.uuid4()),
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
        return self.save_card(card)

    def update_card(self, card_id: str, updates: dict) -> Card | None:
        """Update a card by ID.

        Args:
            card_id: Card's UUID string.
            updates: Fields to update.

        Returns:
            Updated Card or None if not found.
        """
        card = self.get_card(card_id)
        if not card:
            return None

        # Apply updates
        card_dict = card.model_dump()
        card_dict.update(updates)
        updated_card = Card.model_validate(card_dict)

        return self.save_card(updated_card)

    def delete_card(self, card_id: str) -> bool:
        """Delete a card by ID.

        Args:
            card_id: Card's UUID string.

        Returns:
            True if deleted.
        """
        with get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM cards WHERE id = %s AND user_id = %s",
                (card_id, str(self.user_id))
            )
            return cursor.rowcount > 0

    # ==================== PREFERENCES ====================

    def get_preferences(self) -> UserPreferences:
        """Get user preferences.

        Returns:
            UserPreferences (defaults if not set).
        """
        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT * FROM user_preferences WHERE user_id = %s",
                (str(self.user_id),)
            )
            row = cursor.fetchone()

            if not row:
                return UserPreferences()

            return UserPreferences(
                sort_by=row["sort_by"],
                sort_descending=row["sort_descending"],
                group_by_issuer=row["group_by_issuer"],
                auto_enrich_enabled=row["auto_enrich_enabled"],
                enrichment_min_confidence=row["enrichment_min_confidence"],
            )

    def save_preferences(self, prefs: UserPreferences) -> None:
        """Save user preferences.

        Args:
            prefs: Preferences to save.
        """
        with get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_preferences (
                    user_id, sort_by, sort_descending, group_by_issuer,
                    auto_enrich_enabled, enrichment_min_confidence
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    sort_by = EXCLUDED.sort_by,
                    sort_descending = EXCLUDED.sort_descending,
                    group_by_issuer = EXCLUDED.group_by_issuer,
                    auto_enrich_enabled = EXCLUDED.auto_enrich_enabled,
                    enrichment_min_confidence = EXCLUDED.enrichment_min_confidence,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    str(self.user_id), prefs.sort_by, prefs.sort_descending,
                    prefs.group_by_issuer, prefs.auto_enrich_enabled,
                    prefs.enrichment_min_confidence
                )
            )

    def update_preference(self, key: str, value) -> UserPreferences:
        """Update a single preference.

        Args:
            key: Preference key.
            value: New value.

        Returns:
            Updated preferences.
        """
        prefs = self.get_preferences()
        if hasattr(prefs, key):
            setattr(prefs, key, value)
            self.save_preferences(prefs)
        return prefs

    # ==================== EXPORT/IMPORT ====================

    def export_data(self) -> str:
        """Export all cards as JSON.

        Returns:
            JSON string of cards.
        """
        import json
        cards = self.get_all_cards()
        return json.dumps([c.model_dump() for c in cards], indent=2, default=str)

    def import_data(self, json_data: str) -> int:
        """Import cards from JSON.

        Args:
            json_data: JSON string of cards.

        Returns:
            Number of cards imported.
        """
        import json
        data = json.loads(json_data)
        if not isinstance(data, list):
            raise ValueError("Must be a JSON array")

        count = 0
        for item in data:
            try:
                card = Card.model_validate(item)
                # Generate new ID to avoid conflicts
                card.id = str(uuid_module.uuid4())
                self.save_card(card)
                count += 1
            except Exception:
                pass  # Skip invalid cards

        return count
