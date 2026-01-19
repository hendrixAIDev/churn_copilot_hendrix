#!/usr/bin/env python3
"""Enrich the card library by fetching popular credit card data.

This script fetches card information from USCreditCardGuide and other sources,
then generates an updated library.py file with all card templates.

Usage:
    python scripts/enrich_library.py

    # Dry run (preview without writing):
    python scripts/enrich_library.py --dry-run

    # Fetch specific cards only:
    python scripts/enrich_library.py --cards amex_platinum chase_sapphire_reserve
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import extract_from_url
from src.core.models import CardData, Credit
from src.core.exceptions import FetchError, ExtractionError


# Popular credit cards to fetch
# Format: (card_id, display_name, url, fallback_issuer)
# Using official issuer websites where possible for most accurate/up-to-date info
POPULAR_CARDS = [
    # American Express - Official site
    (
        "amex_platinum",
        "American Express Platinum",
        "https://www.americanexpress.com/us/credit-cards/card/platinum/",
        "American Express",
    ),
    (
        "amex_gold",
        "American Express Gold",
        "https://www.americanexpress.com/us/credit-cards/card/gold-card/",
        "American Express",
    ),
    (
        "amex_green",
        "American Express Green",
        "https://www.americanexpress.com/us/credit-cards/card/green/",
        "American Express",
    ),
    (
        "amex_blue_cash_preferred",
        "American Express Blue Cash Preferred",
        "https://www.americanexpress.com/us/credit-cards/card/blue-cash-preferred/",
        "American Express",
    ),
    # Chase - Official site
    (
        "chase_sapphire_preferred",
        "Chase Sapphire Preferred",
        "https://creditcards.chase.com/rewards-credit-cards/sapphire/preferred",
        "Chase",
    ),
    (
        "chase_sapphire_reserve",
        "Chase Sapphire Reserve",
        "https://creditcards.chase.com/rewards-credit-cards/sapphire/reserve",
        "Chase",
    ),
    (
        "chase_freedom_unlimited",
        "Chase Freedom Unlimited",
        "https://creditcards.chase.com/cash-back-credit-cards/freedom/unlimited",
        "Chase",
    ),
    (
        "chase_freedom_flex",
        "Chase Freedom Flex",
        "https://creditcards.chase.com/cash-back-credit-cards/freedom/flex",
        "Chase",
    ),
    (
        "chase_ink_preferred",
        "Chase Ink Business Preferred",
        "https://creditcards.chase.com/business-credit-cards/ink/business-preferred",
        "Chase",
    ),
    # Capital One - Official site
    (
        "capital_one_venture_x",
        "Capital One Venture X",
        "https://www.capitalone.com/credit-cards/venture-x/",
        "Capital One",
    ),
    (
        "capital_one_venture",
        "Capital One Venture",
        "https://www.capitalone.com/credit-cards/venture/",
        "Capital One",
    ),
    (
        "capital_one_savor_one",
        "Capital One SavorOne",
        "https://www.capitalone.com/credit-cards/savorone-dining-rewards/",
        "Capital One",
    ),
    # Citi - Official site
    (
        "citi_strata_premier",
        "Citi Strata Premier",
        "https://www.citi.com/credit-cards/citi-strata-premier-credit-card",
        "Citi",
    ),
    (
        "citi_custom_cash",
        "Citi Custom Cash",
        "https://www.citi.com/credit-cards/citi-custom-cash-credit-card",
        "Citi",
    ),
    (
        "citi_double_cash",
        "Citi Double Cash",
        "https://www.citi.com/credit-cards/citi-double-cash-credit-card",
        "Citi",
    ),
    # Other Popular Cards - Official sites
    (
        "us_bank_altitude_reserve",
        "US Bank Altitude Reserve",
        "https://www.usbank.com/credit-cards/altitude-reserve-visa-infinite-credit-card.html",
        "US Bank",
    ),
    (
        "wells_fargo_autograph",
        "Wells Fargo Autograph",
        "https://creditcards.wellsfargo.com/autograph-visa-credit-card/",
        "Wells Fargo",
    ),
    (
        "bilt_mastercard",
        "Bilt Mastercard",
        "https://www.biltrewards.com/card",
        "Bilt",
    ),
]

# Delay between requests to be respectful to the server
REQUEST_DELAY_SECONDS = 3


def fetch_card(card_id: str, name: str, url: str, fallback_issuer: str | None = None) -> CardData | None:
    """Fetch card data from URL.

    Args:
        card_id: Unique identifier for the card.
        name: Display name of the card.
        url: URL to fetch card data from.
        fallback_issuer: Fallback issuer name if extraction fails to get one.

    Returns:
        CardData if successful, None if failed.
    """
    print(f"  Fetching: {name}...")
    try:
        card_data = extract_from_url(url)

        # Validate required fields
        if not card_data.name:
            print(f"    FAILED: No card name extracted")
            return None
        if not card_data.issuer:
            if fallback_issuer:
                # Use fallback issuer if provided
                print(f"    WARNING: No issuer extracted, using fallback: {fallback_issuer}")
                card_data = CardData(
                    name=card_data.name,
                    issuer=fallback_issuer,
                    annual_fee=card_data.annual_fee,
                    signup_bonus=card_data.signup_bonus,
                    credits=card_data.credits,
                )
            else:
                print(f"    FAILED: No issuer extracted")
                return None

        print(f"    OK: {card_data.name} (${card_data.annual_fee} AF, {len(card_data.credits)} credits)")
        return card_data
    except (FetchError, ExtractionError) as e:
        error_msg = str(e)
        if "451" in error_msg:
            print(f"    BLOCKED: Site unavailable via Jina Reader (legal restriction)")
        else:
            print(f"    FAILED: {e}")
        return None
    except Exception as e:
        print(f"    ERROR: {type(e).__name__}: {e}")
        return None


def format_credit(credit: Credit, indent: str = "            ") -> str:
    """Format a Credit object as Python code."""
    lines = [f"{indent}Credit("]
    lines.append(f'{indent}    name="{credit.name}",')
    lines.append(f"{indent}    amount={credit.amount},")
    lines.append(f'{indent}    frequency="{credit.frequency}",')
    if credit.notes:
        # Escape quotes in notes
        notes = credit.notes.replace('"', '\\"')
        lines.append(f'{indent}    notes="{notes}",')
    lines.append(f"{indent}),")
    return "\n".join(lines)


def generate_library_code(cards: dict[str, CardData]) -> str:
    """Generate Python code for the library module.

    Args:
        cards: Dictionary mapping card_id to CardData.

    Returns:
        Python source code for library.py.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        '"""Card template library for ChurnPilot.',
        "",
        "This module provides pre-defined card templates that users can select",
        "to quickly add cards with all benefits pre-populated.",
        "",
        f"Auto-generated on: {timestamp}",
        '"""',
        "",
        "from pydantic import BaseModel, Field",
        "",
        "from src.core.models import Credit",
        "",
        "",
        "class CardTemplate(BaseModel):",
        '    """A card template with pre-defined benefits and details."""',
        "",
        '    id: str = Field(..., description="Unique template identifier")',
        '    name: str = Field(..., description="Full card name")',
        '    issuer: str = Field(..., description="Card issuer")',
        '    annual_fee: int = Field(..., description="Annual fee in dollars")',
        "    credits: list[Credit] = Field(",
        '        default_factory=list, description="Recurring credits/perks"',
        "    )",
        "",
        "",
        "# Card template library",
        "CARD_LIBRARY: dict[str, CardTemplate] = {",
    ]

    # Add each card
    for card_id, card_data in cards.items():
        lines.append(f'    "{card_id}": CardTemplate(')
        lines.append(f'        id="{card_id}",')
        # Escape quotes in name
        name = card_data.name.replace('"', '\\"')
        lines.append(f'        name="{name}",')
        issuer = card_data.issuer.replace('"', '\\"')
        lines.append(f'        issuer="{issuer}",')
        lines.append(f"        annual_fee={card_data.annual_fee},")

        if card_data.credits:
            lines.append("        credits=[")
            for credit in card_data.credits:
                lines.append(format_credit(credit))
            lines.append("        ],")
        else:
            lines.append("        credits=[],")

        lines.append("    ),")

    lines.append("}")
    lines.append("")
    lines.append("")

    # Add helper functions
    lines.extend([
        "def get_all_templates() -> list[CardTemplate]:",
        '    """Get all available card templates.',
        "",
        "    Returns:",
        "        List of all card templates in the library.",
        '    """',
        "    return list(CARD_LIBRARY.values())",
        "",
        "",
        "def get_template(template_id: str) -> CardTemplate | None:",
        '    """Get a specific card template by ID.',
        "",
        "    Args:",
        "        template_id: The unique template identifier.",
        "",
        "    Returns:",
        "        The card template if found, None otherwise.",
        '    """',
        "    return CARD_LIBRARY.get(template_id)",
        "",
        "",
        "def get_template_choices() -> list[tuple[str, str]]:",
        '    """Get template choices formatted for UI dropdowns.',
        "",
        "    Returns:",
        "        List of (id, display_name) tuples for each template.",
        '    """',
        '    return [(t.id, f"{t.name} ({t.issuer})") for t in CARD_LIBRARY.values()]',
        "",
    ])

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch popular credit card data and update the library"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to file",
    )
    parser.add_argument(
        "--cards",
        nargs="+",
        help="Specific card IDs to fetch (default: all)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("src/core/library.py"),
        help="Output file path (default: src/core/library.py)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ChurnPilot Library Enrichment")
    print("=" * 60)

    # Filter cards if specific ones requested
    cards_to_fetch = POPULAR_CARDS
    if args.cards:
        cards_to_fetch = [
            (cid, name, url, issuer)
            for cid, name, url, issuer in POPULAR_CARDS
            if cid in args.cards
        ]
        if not cards_to_fetch:
            print(f"ERROR: No matching cards found for: {args.cards}")
            print(f"Available cards: {[c[0] for c in POPULAR_CARDS]}")
            return 1

    print(f"\nFetching {len(cards_to_fetch)} cards...")
    print("-" * 60)

    # Fetch all cards
    fetched_cards: dict[str, CardData] = {}
    failed_cards: list[str] = []

    for i, (card_id, name, url, fallback_issuer) in enumerate(cards_to_fetch):
        card_data = fetch_card(card_id, name, url, fallback_issuer)

        if card_data:
            fetched_cards[card_id] = card_data
        else:
            failed_cards.append(card_id)

        # Delay between requests (except for last one)
        if i < len(cards_to_fetch) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)

    print("-" * 60)
    print(f"\nResults: {len(fetched_cards)} succeeded, {len(failed_cards)} failed")

    if failed_cards:
        print(f"Failed cards: {failed_cards}")

    if not fetched_cards:
        print("ERROR: No cards fetched successfully. Aborting.")
        return 1

    # Generate library code
    print(f"\nGenerating library code...")
    library_code = generate_library_code(fetched_cards)

    if args.dry_run:
        print("\n[DRY RUN] Would write to:", args.output)
        print("-" * 60)
        # Show first 50 lines
        preview_lines = library_code.split("\n")[:50]
        print("\n".join(preview_lines))
        if len(library_code.split("\n")) > 50:
            print(f"... ({len(library_code.split(chr(10))) - 50} more lines)")
    else:
        # Write to file
        args.output.write_text(library_code, encoding="utf-8")
        print(f"Wrote library to: {args.output}")
        print(f"Total cards: {len(fetched_cards)}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
