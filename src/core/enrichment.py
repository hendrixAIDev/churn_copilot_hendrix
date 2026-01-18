"""Auto-enrichment of card data from library templates.

This module provides functionality to automatically enrich extracted card data
with benefits from the card library. When a card is extracted from a URL,
text, or spreadsheet, we match it to a library template and fill in missing
credits/benefits.
"""

from typing import Tuple
from .models import CardData, Credit
from .library import CardTemplate, CARD_LIBRARY
from .normalize import normalize_issuer, simplify_card_name


class MatchResult:
    """Result of matching a card to a library template."""

    def __init__(self, template_id: str | None, confidence: float, template: CardTemplate | None = None):
        """Initialize match result.

        Args:
            template_id: ID of matched template, or None if no match.
            confidence: Confidence score from 0.0 to 1.0.
            template: The matched template object (for convenience).
        """
        self.template_id = template_id
        self.confidence = confidence
        self.template = template

    def __repr__(self) -> str:
        if self.template_id:
            return f"MatchResult(template_id='{self.template_id}', confidence={self.confidence:.2f})"
        return f"MatchResult(no match, confidence={self.confidence:.2f})"


def match_to_library_with_confidence(
    name: str,
    issuer: str,
    min_confidence: float = 0.6,
) -> MatchResult:
    """Match a card to a library template with confidence scoring.

    Args:
        name: Card name from extraction.
        issuer: Card issuer.
        min_confidence: Minimum confidence threshold (default: 0.6).

    Returns:
        MatchResult with template_id, confidence, and template object.

    Confidence levels:
        1.0 = Exact name match
        0.9 = Simplified name match
        0.8 = All key words present
        0.7 = Most key words present
        0.0 = No match
    """
    # Normalize inputs
    name_lower = name.lower().strip()
    issuer_normalized = normalize_issuer(issuer)
    name_simplified = simplify_card_name(name, issuer).lower()

    best_match_id: str | None = None
    best_confidence = 0.0
    best_template: CardTemplate | None = None

    # Try to find matching template
    for template_id, template in CARD_LIBRARY.items():
        # Check issuer match first (required)
        template_issuer_normalized = normalize_issuer(template.issuer)
        if template_issuer_normalized.lower() != issuer_normalized.lower():
            continue

        # Check name match
        template_name_lower = template.name.lower()
        template_simplified = simplify_card_name(template.name, template.issuer).lower()

        # Exact match (confidence: 1.0)
        if name_lower == template_name_lower:
            return MatchResult(template_id, 1.0, template)

        # Simplified name exact match (confidence: 0.9)
        if name_simplified and name_simplified == template_simplified:
            if 0.9 > best_confidence:
                best_match_id = template_id
                best_confidence = 0.9
                best_template = template

        # Key words match (confidence: 0.7-0.85)
        if template_simplified:
            key_words = template_simplified.split()
            if len(key_words) > 0:
                matching_words = sum(1 for word in key_words if word in name_lower)
                word_match_ratio = matching_words / len(key_words)

                if word_match_ratio >= 0.8:  # 80%+ key words match
                    confidence = 0.75 + (word_match_ratio - 0.8) * 0.5  # 0.75-0.85
                    if confidence > best_confidence:
                        best_match_id = template_id
                        best_confidence = confidence
                        best_template = template
                elif word_match_ratio >= 0.6 and len(key_words) >= 2:  # 60%+ match
                    confidence = 0.65 + (word_match_ratio - 0.6) * 0.5  # 0.65-0.75
                    if confidence > best_confidence:
                        best_match_id = template_id
                        best_confidence = confidence
                        best_template = template

    # Check if best match meets minimum confidence
    if best_confidence >= min_confidence:
        return MatchResult(best_match_id, best_confidence, best_template)

    return MatchResult(None, 0.0, None)


def enrich_card_data(
    card_data: CardData,
    min_confidence: float = 0.7,
) -> Tuple[CardData, MatchResult]:
    """Enrich card data with benefits from library template.

    Strategy:
    - Match card to library template using name and issuer
    - Add credits from template that are NOT already in extracted data
    - Never overwrite existing credits from extraction
    - Prefer extracted annual fee over template (user might have old rate)

    Args:
        card_data: Extracted card data to enrich.
        min_confidence: Minimum confidence for enrichment (default: 0.7).

    Returns:
        Tuple of (enriched_card_data, match_result).
        If no match or low confidence, returns original card_data unchanged.

    Examples:
        >>> # Extracted card with 2 credits
        >>> card_data = CardData(name="Amex Platinum", issuer="American Express", annual_fee=695, credits=[...2 credits...])
        >>> enriched, match = enrich_card_data(card_data)
        >>> len(enriched.credits)  # Now has 8 credits (2 extracted + 6 from library)
        8
        >>> match.template_id
        'amex_platinum'
        >>> match.confidence
        0.9
    """
    # Try to match to library
    match_result = match_to_library_with_confidence(
        card_data.name,
        card_data.issuer,
        min_confidence=min_confidence,
    )

    # If no match or low confidence, return original
    if not match_result.template or not match_result.template_id:
        return (card_data, match_result)

    # Build enriched data
    enriched_data = card_data.model_copy(deep=True)

    # Get existing credit names (to avoid duplicates)
    existing_credit_names = {credit.name.lower() for credit in card_data.credits}

    # Add credits from template that don't exist in extracted data
    credits_added = 0
    for template_credit in match_result.template.credits:
        # Check if this credit already exists (case-insensitive)
        if template_credit.name.lower() not in existing_credit_names:
            enriched_data.credits.append(template_credit.model_copy())
            credits_added += 1

    # Note: We keep the extracted annual_fee, not the template fee
    # (user might have negotiated rate, retention offer, first year waived, etc.)

    return (enriched_data, match_result)


def get_enrichment_summary(
    original_data: CardData,
    enriched_data: CardData,
    match_result: MatchResult,
) -> str:
    """Get human-readable summary of enrichment.

    Args:
        original_data: Original extracted card data.
        enriched_data: Enriched card data.
        match_result: Match result from enrichment.

    Returns:
        Summary string for display to user.

    Examples:
        >>> summary = get_enrichment_summary(original, enriched, match)
        >>> print(summary)
        "Auto-enriched from 'American Express Platinum' template (90% match): Added 6 credits"
    """
    if not match_result.template:
        return "No enrichment (no library match found)"

    credits_added = len(enriched_data.credits) - len(original_data.credits)

    if credits_added == 0:
        return f"Matched to '{match_result.template.name}' template ({int(match_result.confidence * 100)}% match) but no new credits to add"

    return f"Auto-enriched from '{match_result.template.name}' template ({int(match_result.confidence * 100)}% match): Added {credits_added} credit(s)"


def should_enrich_card(name: str, issuer: str, min_confidence: float = 0.7) -> bool:
    """Quick check if a card would benefit from enrichment.

    Args:
        name: Card name.
        issuer: Card issuer.
        min_confidence: Minimum confidence threshold.

    Returns:
        True if card matches a template with sufficient confidence, False otherwise.
    """
    match_result = match_to_library_with_confidence(name, issuer, min_confidence)
    return match_result.template is not None and match_result.template_id is not None
