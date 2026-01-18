"""Card template library for ChurnPilot.

This module provides pre-defined card templates that users can select
to quickly add cards with all benefits pre-populated.

Auto-generated on: 2026-01-16 17:04:44
"""

from pydantic import BaseModel, Field

from src.core.models import Credit


class CardTemplate(BaseModel):
    """A card template with pre-defined benefits and details."""

    id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Full card name")
    issuer: str = Field(..., description="Card issuer")
    annual_fee: int = Field(..., description="Annual fee in dollars")
    credits: list[Credit] = Field(
        default_factory=list, description="Recurring credits/perks"
    )


# Card template library
CARD_LIBRARY: dict[str, CardTemplate] = {
    "amex_platinum": CardTemplate(
        id="amex_platinum",
        name="American Express Platinum",
        issuer="American Express",
        annual_fee=895,
        credits=[
            Credit(name="Uber Credit", amount=15.0, frequency="monthly", notes="$35 in December"),
            Credit(name="Saks Fifth Avenue Credit", amount=50.0, frequency="semi-annually"),
            Credit(name="Airline Fee Credit", amount=200.0, frequency="annual", notes="Incidental fees only"),
            Credit(name="Digital Entertainment Credit", amount=20.0, frequency="monthly"),
            Credit(name="Hotel Credit", amount=200.0, frequency="annual", notes="FHR or THC"),
            Credit(name="CLEAR Plus Credit", amount=189.0, frequency="annual"),
            Credit(name="Equinox Credit", amount=25.0, frequency="monthly", notes="Up to $300/year"),
            Credit(name="Walmart+ Credit", amount=12.95, frequency="monthly"),
        ],
    ),
    "amex_gold": CardTemplate(
        id="amex_gold",
        name="American Express Gold",
        issuer="American Express",
        annual_fee=250,
        credits=[
            Credit(name="Uber Cash", amount=10.0, frequency="monthly", notes="US only"),
            Credit(name="Dining Credit", amount=10.0, frequency="monthly", notes="Grubhub, Seamless, Cheesecake Factory, etc."),
            Credit(name="Dunkin Credit", amount=7.0, frequency="monthly"),
        ],
    ),
    "amex_green": CardTemplate(
        id="amex_green",
        name="American Express Green",
        issuer="American Express",
        annual_fee=150,
        credits=[
            Credit(name="LoungeBuddy Credit", amount=100.0, frequency="annual"),
            Credit(name="CLEAR Plus Credit", amount=189.0, frequency="annual"),
        ],
    ),
    "amex_blue_cash_preferred": CardTemplate(
        id="amex_blue_cash_preferred",
        name="Blue Cash Preferred",
        issuer="American Express",
        annual_fee=0,
        credits=[
            Credit(name="Disney Bundle Credit", amount=7.0, frequency="monthly"),
        ],
    ),
    "chase_sapphire_preferred": CardTemplate(
        id="chase_sapphire_preferred",
        name="Chase Sapphire Preferred Credit Card",
        issuer="Chase",
        annual_fee=95,
        credits=[
            Credit(
                name="Chase Travel Hotel Credit",
                amount=50.0,
                frequency="annual",
                notes="Statement credits for hotel stays purchased through Chase Travel",
            ),
        ],
    ),
    "chase_sapphire_reserve": CardTemplate(
        id="chase_sapphire_reserve",
        name="Chase Sapphire Reserve",
        issuer="Chase",
        annual_fee=795,
        credits=[
            Credit(
                name="Annual Travel Credit",
                amount=300.0,
                frequency="annual",
                notes="Statement credits for travel purchases each account anniversary year",
            ),
            Credit(
                name="The Edit Credit",
                amount=500.0,
                frequency="annual",
                notes="Up to $250 in statement credits from January through June and again from July through December for prepaid bookings with The Edit. Two-night minimum.",
            ),
        ],
    ),
    "chase_freedom_unlimited": CardTemplate(
        id="chase_freedom_unlimited",
        name="Chase Freedom Unlimited Credit Card",
        issuer="Chase",
        annual_fee=0,
        credits=[],
    ),
    "chase_freedom_flex": CardTemplate(
        id="chase_freedom_flex",
        name="Chase Freedom Flex Credit Card",
        issuer="Chase",
        annual_fee=0,
        credits=[],
    ),
    "chase_ink_preferred": CardTemplate(
        id="chase_ink_preferred",
        name="Ink Business Preferred Credit Card",
        issuer="Chase",
        annual_fee=95,
        credits=[],
    ),
    "capital_one_venture_x": CardTemplate(
        id="capital_one_venture_x",
        name="Capital One Venture X",
        issuer="Capital One",
        annual_fee=395,
        credits=[
            Credit(name="Capital One Travel Credit", amount=300.0, frequency="annual", notes="Only on Capital One Travel portal"),
            Credit(name="Global Entry/TSA PreCheck Credit", amount=100.0, frequency="annual", notes="Once every 4 years"),
            Credit(name="Anniversary Bonus", amount=10000.0, frequency="annual", notes="10,000 miles on each account anniversary"),
        ],
    ),
    "capital_one_venture": CardTemplate(
        id="capital_one_venture",
        name="Capital One Venture",
        issuer="Capital One",
        annual_fee=95,
        credits=[
            Credit(name="Global Entry/TSA PreCheck Credit", amount=100.0, frequency="annual", notes="Once every 4 years"),
        ],
    ),
    "capital_one_savor_one": CardTemplate(
        id="capital_one_savor_one",
        name="Capital One SavorOne",
        issuer="Capital One",
        annual_fee=0,
        credits=[],
    ),
    "citi_premier": CardTemplate(
        id="citi_premier",
        name="Citi Strata Premier Card",
        issuer="Citi",
        annual_fee=95,
        credits=[
            Credit(
                name="Annual Hotel Benefit",
                amount=100.0,
                frequency="annual",
                notes="Once per calendar year, $100 off a single hotel stay of $500 or more when booked through cititravel.com",
            ),
        ],
    ),
    "citi_custom_cash": CardTemplate(
        id="citi_custom_cash",
        name="Citi Custom Cash Card",
        issuer="Citi",
        annual_fee=0,
        credits=[],
    ),
    "citi_double_cash": CardTemplate(
        id="citi_double_cash",
        name="Citi Double Cash Card",
        issuer="Citi",
        annual_fee=0,
        credits=[],
    ),
    "us_bank_altitude_reserve": CardTemplate(
        id="us_bank_altitude_reserve",
        name="US Bank Altitude Reserve",
        issuer="US Bank",
        annual_fee=400,
        credits=[
            Credit(name="Travel Credit", amount=325.0, frequency="annual"),
            Credit(name="Global Entry/TSA PreCheck Credit", amount=100.0, frequency="annual", notes="Once every 4 years"),
        ],
    ),
    "wells_fargo_autograph": CardTemplate(
        id="wells_fargo_autograph",
        name="Wells Fargo Autograph",
        issuer="Wells Fargo",
        annual_fee=0,
        credits=[
            Credit(name="Cell Phone Protection", amount=600.0, frequency="annual", notes="Up to $600 per claim, 2 claims per year"),
        ],
    ),
    "bilt_mastercard": CardTemplate(
        id="bilt_mastercard",
        name="Bilt Mastercard",
        issuer="Bilt",
        annual_fee=0,
        credits=[
            Credit(name="Lyft Credit", amount=2.5, frequency="monthly", notes="5 rides per month"),
        ],
    ),
}


def get_all_templates() -> list[CardTemplate]:
    """Get all available card templates.

    Returns:
        List of all card templates in the library.
    """
    return list(CARD_LIBRARY.values())


def get_template(template_id: str) -> CardTemplate | None:
    """Get a specific card template by ID.

    Args:
        template_id: The unique template identifier.

    Returns:
        The card template if found, None otherwise.
    """
    return CARD_LIBRARY.get(template_id)


def get_template_choices() -> list[tuple[str, str]]:
    """Get template choices formatted for UI dropdowns.

    Returns:
        List of (id, display_name) tuples for each template.
    """
    return [(t.id, f"{t.name} ({t.issuer})") for t in CARD_LIBRARY.values()]
