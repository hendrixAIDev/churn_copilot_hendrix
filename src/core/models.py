"""Pydantic data models for ChurnPilot."""

from datetime import date
from pydantic import BaseModel, Field


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


class Card(BaseModel):
    """A credit card with all tracked information."""

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Card name (e.g., 'Chase Sapphire Preferred')")
    issuer: str = Field(..., description="Card issuer (Chase, Amex, etc.)")
    annual_fee: int = Field(default=0, description="Annual fee in dollars")
    signup_bonus: SignupBonus | None = Field(default=None, description="SUB details")
    credits: list[Credit] = Field(default_factory=list, description="Card credits/perks")
    opened_date: date | None = Field(default=None, description="Account open date")
    annual_fee_date: date | None = Field(
        default=None, description="Next annual fee due date"
    )
    notes: str | None = Field(default=None, description="User notes")
    raw_text: str | None = Field(
        default=None, description="Original text used for extraction"
    )


class CardData(BaseModel):
    """Intermediate extraction result before full Card creation."""

    name: str
    issuer: str
    annual_fee: int = 0
    signup_bonus: SignupBonus | None = None
    credits: list[Credit] = Field(default_factory=list)
