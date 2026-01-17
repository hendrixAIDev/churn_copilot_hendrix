"""Card name and issuer normalization for ChurnPilot.

This module provides functions to normalize card names and issuers
to ensure consistency across manually imported and library cards.
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .library import CardTemplate

# Issuer name normalization mapping
# Maps variations to canonical issuer names
ISSUER_ALIASES: dict[str, str] = {
    # American Express variations
    "amex": "American Express",
    "american express": "American Express",
    "americanexpress": "American Express",
    # Chase variations
    "chase": "Chase",
    "chase bank": "Chase",
    "jpmorgan chase": "Chase",
    # Capital One variations
    "capital one": "Capital One",
    "capitalone": "Capital One",
    "cap one": "Capital One",
    # Citi variations
    "citi": "Citi",
    "citibank": "Citi",
    "citigroup": "Citi",
    # Other issuers
    "discover": "Discover",
    "bank of america": "Bank of America",
    "bofa": "Bank of America",
    "wells fargo": "Wells Fargo",
    "us bank": "US Bank",
    "usbank": "US Bank",
    "barclays": "Barclays",
    "bilt": "Bilt",
    "bilt rewards": "Bilt",
}

# Patterns to remove from card names (case-insensitive)
CARD_NAME_REMOVE_PATTERNS = [
    r"\bcredit\s*card\b",
    r"\bcard\b",  # Remove "card" anywhere
    r"®",
    r"™",
    r"\bfrom\s+",
    r"\bthe\b",
    r"\s+$",
    r"^\s+",
]

# Issuer prefixes/suffixes to remove from card names
ISSUER_PATTERNS = [
    "american express",
    "amex",
    "chase",
    "capital one",
    "capitalone",
    "citi",
    "citibank",
    "discover",
    "bank of america",
    "wells fargo",
    "us bank",
    "barclays",
    "bilt",
]


def normalize_issuer(issuer: str) -> str:
    """Normalize an issuer name to canonical form.

    Args:
        issuer: Raw issuer name from extraction or user input.

    Returns:
        Normalized issuer name.

    Examples:
        >>> normalize_issuer("AMEX")
        'American Express'
        >>> normalize_issuer("Chase Bank")
        'Chase'
    """
    if not issuer:
        return issuer

    # Lowercase for lookup
    issuer_lower = issuer.lower().strip()

    # Check aliases
    if issuer_lower in ISSUER_ALIASES:
        return ISSUER_ALIASES[issuer_lower]

    # Return original with title case if no match
    return issuer.strip()


def simplify_card_name(name: str, issuer: str | None = None) -> str:
    """Simplify a card name by removing issuer and common suffixes.

    Args:
        name: Full card name (e.g., "Chase Sapphire Preferred Credit Card").
        issuer: Optional issuer to remove from name.

    Returns:
        Simplified card name (e.g., "Sapphire Preferred").

    Examples:
        >>> simplify_card_name("Chase Sapphire Preferred Credit Card", "Chase")
        'Sapphire Preferred'
        >>> simplify_card_name("The Platinum Card from American Express", "American Express")
        'Platinum'
    """
    if not name:
        return name

    result = name.strip()

    # Remove common patterns
    for pattern in CARD_NAME_REMOVE_PATTERNS:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)

    # Remove issuer name from card name
    if issuer:
        # Try exact issuer match
        result = re.sub(rf"\b{re.escape(issuer)}\b", "", result, flags=re.IGNORECASE)

    # Remove common issuer patterns
    for issuer_pattern in ISSUER_PATTERNS:
        result = re.sub(rf"\b{re.escape(issuer_pattern)}\b", "", result, flags=re.IGNORECASE)

    # Clean up whitespace
    result = re.sub(r"\s+", " ", result).strip()

    # If we removed everything, return original name
    if not result:
        return name.strip()

    return result


def match_to_library_template(
    name: str,
    issuer: str,
) -> str | None:
    """Try to match a card to a library template.

    Args:
        name: Card name from extraction.
        issuer: Card issuer.

    Returns:
        Template ID if matched, None otherwise.
    """
    # Import here to avoid circular imports
    from .library import CARD_LIBRARY

    # Normalize inputs
    name_lower = name.lower()
    issuer_normalized = normalize_issuer(issuer)
    name_simplified = simplify_card_name(name, issuer).lower()

    # Try to find matching template
    for template_id, template in CARD_LIBRARY.items():
        # Check issuer match first
        if template.issuer.lower() != issuer_normalized.lower():
            continue

        # Check name match
        template_name_lower = template.name.lower()
        template_simplified = simplify_card_name(template.name, template.issuer).lower()

        # Exact match
        if name_lower == template_name_lower:
            return template_id

        # Simplified name match
        if name_simplified == template_simplified:
            return template_id

        # Key words match (e.g., "platinum", "sapphire preferred", "venture x")
        key_words = template_simplified.split()
        if all(word in name_lower for word in key_words):
            return template_id

    return None


def get_display_name(name: str, issuer: str | None = None) -> str:
    """Get display-friendly card name without issuer.

    This is the main function to use when displaying card names
    in the UI where issuer is shown separately.

    Args:
        name: Full card name.
        issuer: Card issuer (shown separately in UI).

    Returns:
        Simplified name for display.
    """
    return simplify_card_name(name, issuer)
