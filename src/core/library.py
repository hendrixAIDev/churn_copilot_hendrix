"""Card template library for ChurnPilot.

This module provides pre-defined card templates that users can select
to quickly add cards with all benefits pre-populated.

Last updated: 2026-01-18 (verified against current card offerings)
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
            Credit(name="Hotel Credit", amount=300.0, frequency="semi-annually", notes="FHR or THC prepaid bookings (THC requires 2-night minimum)"),
            Credit(name="Uber Credit", amount=200.0, frequency="annual", notes="$200 Uber Cash issued monthly for rides/Uber Eats"),
            Credit(name="Uber One Credit", amount=120.0, frequency="annual", notes="Auto-renewing Uber One membership"),
            Credit(name="Resy Credit", amount=100.0, frequency="quarterly", notes="At U.S. Resy restaurants and eligible Resy purchases"),
            Credit(name="Digital Entertainment Credit", amount=300.0, frequency="annual", notes="Disney+, Hulu, ESPN+, Peacock, WSJ, NYT"),
            Credit(name="lululemon Credit", amount=75.0, frequency="quarterly", notes="At lululemon retail stores (excl. outlets) and lululemon.com"),
            Credit(name="Airline Fee Credit", amount=200.0, frequency="annual", notes="Incidental fees with selected airline"),
            Credit(name="CLEAR Plus Credit", amount=209.0, frequency="annual"),
            Credit(name="Saks Fifth Avenue Credit", amount=50.0, frequency="semi-annually"),
        ],
    ),
    "amex_gold": CardTemplate(
        id="amex_gold",
        name="American Express Gold",
        issuer="American Express",
        annual_fee=325,
        credits=[
            Credit(name="Uber Cash", amount=10.0, frequency="monthly", notes="Uber Eats and Uber rides"),
            Credit(name="Dining Credit", amount=10.0, frequency="monthly", notes="GrubHub, Cheesecake Factory, Goldbelly, Wine.com, Five Guys"),
            Credit(name="Dunkin Credit", amount=7.0, frequency="monthly"),
            Credit(name="Resy Credit", amount=50.0, frequency="semi-annually", notes="At U.S. Resy restaurants"),
            Credit(name="Hotel Credit", amount=100.0, frequency="annual", notes="The Hotel Collection bookings (2+ nights)"),
        ],
    ),
    "amex_green": CardTemplate(
        id="amex_green",
        name="American Express Green",
        issuer="American Express",
        annual_fee=150,
        credits=[
            Credit(name="CLEAR Plus Credit", amount=209.0, frequency="annual", notes="Covers CLEAR Plus membership"),
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
            Credit(
                name="DashPass Membership",
                amount=120.0,
                frequency="annual",
                notes="Complimentary DashPass for 12 months (through Dec 2027)",
            ),
            Credit(
                name="DoorDash Promo Credit",
                amount=10.0,
                frequency="monthly",
                notes="$10 monthly for groceries/retail via DoorDash (through Dec 2027)",
            ),
        ],
    ),
    "chase_sapphire_reserve": CardTemplate(
        id="chase_sapphire_reserve",
        name="Chase Sapphire Reserve",
        issuer="Chase",
        annual_fee=795,
        credits=[
            Credit(name="Annual Travel Credit", amount=300.0, frequency="annual", notes="Any travel purchase"),
            Credit(name="The Edit Credit", amount=250.0, frequency="semi-annually", notes="Prepaid bookings with The Edit hotels via Chase Travel"),
            Credit(name="Select Hotel Credit", amount=250.0, frequency="annual", notes="IHG, Montage, Pendry, Omni, Virgin Hotels, Minor Hotels, Pan Pacific (2-night min, 2026 only)"),
            Credit(name="Dining Credit", amount=150.0, frequency="semi-annually", notes="Sapphire Reserve Exclusive Tables restaurants"),
            Credit(name="StubHub/Viagogo Credit", amount=150.0, frequency="semi-annually", notes="Activation required"),
            Credit(name="Peloton Credit", amount=10.0, frequency="monthly", notes="Through Dec 2027, activation required"),
            Credit(name="Global Entry/TSA PreCheck Credit", amount=120.0, frequency="annual", notes="Once every 4 years"),
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
            Credit(name="Capital One Travel Credit", amount=300.0, frequency="annual", notes="Capital One Travel portal bookings"),
            Credit(name="Global Entry/TSA PreCheck Credit", amount=120.0, frequency="annual", notes="Once every 4 years"),
            Credit(name="Anniversary Bonus", amount=10000.0, frequency="annual", notes="10,000 miles on each account anniversary"),
        ],
    ),
    "capital_one_venture": CardTemplate(
        id="capital_one_venture",
        name="Capital One Venture",
        issuer="Capital One",
        annual_fee=95,
        credits=[
            Credit(name="Global Entry/TSA PreCheck Credit", amount=120.0, frequency="annual", notes="Once every 4 years"),
            Credit(name="Lifestyle Collection Credit", amount=50.0, frequency="annual", notes="At Lifestyle Collection hotels or vacation rentals"),
        ],
    ),
    "capital_one_savor_one": CardTemplate(
        id="capital_one_savor_one",
        name="Capital One SavorOne",
        issuer="Capital One",
        annual_fee=0,
        credits=[],
    ),
    "citi_strata_premier": CardTemplate(
        id="citi_strata_premier",
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
            Credit(name="Travel Credit", amount=325.0, frequency="annual", notes="Now restricted to U.S. Bank Travel Center purchases"),
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
