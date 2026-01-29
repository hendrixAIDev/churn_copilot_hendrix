"""Pydantic data models for ChurnPilot."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class User(BaseModel):
    """A user account."""

    id: UUID = Field(..., description="Unique identifier")
    email: str = Field(..., description="User email (unique, lowercase)")
    created_at: datetime | None = Field(default=None, description="Account creation time")
    updated_at: datetime | None = Field(default=None, description="Last update time")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip() if v else v


class Credit(BaseModel):
    """A recurring credit or perk associated with a card."""

    name: str = Field(..., description="Credit name (e.g., 'Uber Credit')")
    amount: float = Field(..., description="Credit amount in dollars")
    frequency: str = Field(
        default="monthly", description="How often credit is available"
    )
    notes: str | None = Field(default=None, description="Additional details")


class SignupBonus(BaseModel):
    """Sign-up bonus (SUB) details for a card."""

    points_or_cash: str = Field(
        ..., description="Bonus amount (e.g., '60,000 points' or '$200 cash back')"
    )
    spend_requirement: float = Field(..., description="Required spend in dollars")
    time_period_days: int = Field(
        ..., description="Days to meet spend requirement (typically 90)"
    )
    deadline: date | None = Field(
        default=None, description="Calculated deadline to meet spend"
    )


class CreditUsage(BaseModel):
    """Tracks usage of a single credit/benefit."""

    # Period when the credit was last marked as used (e.g., "2024-01", "2024-Q1", "2024-H1", "2024")
    last_used_period: str | None = Field(
        default=None,
        description="Period when credit was last used"
    )
    # If set, reminder is snoozed until this date
    reminder_snoozed_until: date | None = Field(
        default=None,
        description="Date until which the reminder is snoozed"
    )


class RetentionOffer(BaseModel):
    """Tracks a retention offer received from an issuer."""

    date_called: date = Field(..., description="Date of retention call")
    offer_details: str = Field(
        ..., description="Offer details (e.g., '20,000 points after $2,000 spend')"
    )
    accepted: bool = Field(..., description="Whether offer was accepted")
    notes: str | None = Field(default=None, description="Additional notes")


class ProductChange(BaseModel):
    """Tracks a product change (upgrade/downgrade) for a card."""

    date_changed: date = Field(..., description="Date of product change")
    from_product: str = Field(..., description="Original card name")
    to_product: str = Field(..., description="New card name after change")
    reason: str | None = Field(
        default=None,
        description="Reason for change (e.g., 'Avoid annual fee', 'Upgrade for SUB')"
    )
    notes: str | None = Field(default=None, description="Additional notes")


class Card(BaseModel):
    """A credit card with all tracked information."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Card name (e.g., 'Chase Sapphire Preferred')")
    nickname: str | None = Field(default=None, description="User-defined nickname")
    issuer: str = Field(..., description="Card issuer (Chase, Amex, etc.)")
    annual_fee: int = Field(default=0, description="Annual fee in dollars")
    signup_bonus: SignupBonus | None = Field(default=None, description="SUB details")
    sub_spend_progress: float | None = Field(
        default=None, description="Current spending towards SUB requirement"
    )
    sub_achieved: bool = Field(default=False, description="Whether SUB has been earned")
    credits: list[Credit] = Field(default_factory=list, description="Card credits/perks")
    opened_date: date | None = Field(default=None, description="Account open date")
    annual_fee_date: date | None = Field(
        default=None, description="Next annual fee due date"
    )
    notes: str | None = Field(default=None, description="User notes")
    raw_text: str | None = Field(
        default=None, description="Original text used for extraction"
    )
    template_id: str | None = Field(
        default=None, description="Library template ID if matched"
    )
    created_at: datetime | None = Field(
        default=None, description="When the card was added to the system"
    )
    credit_usage: dict[str, CreditUsage] = Field(
        default_factory=dict,
        description="Tracks usage of each credit by name"
    )
    benefits_reminder_snoozed_until: date | None = Field(
        default=None,
        description="If set, all benefit reminders snoozed until this date"
    )
    is_business: bool = Field(
        default=False,
        description="Whether this is a business card (affects 5/24 calculation)"
    )
    closed_date: date | None = Field(
        default=None,
        description="Date the account was closed"
    )
    retention_offers: list[RetentionOffer] = Field(
        default_factory=list,
        description="History of retention offers received"
    )
    product_change_history: list[ProductChange] = Field(
        default_factory=list,
        description="History of product changes (upgrades/downgrades)"
    )


class CardData(BaseModel):
    """Intermediate extraction result before full Card creation."""

    name: str
    issuer: str
    annual_fee: int = 0
    signup_bonus: SignupBonus | None = None
    credits: list[Credit] = Field(default_factory=list)
