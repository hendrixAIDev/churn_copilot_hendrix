"""Core business logic - framework agnostic."""

from .models import Card, SignupBonus, Credit, CardData, CreditUsage
from .storage import CardStorage
from .preprocessor import preprocess_text, get_char_reduction
from .fetcher import fetch_card_page, get_allowed_domains
from .pipeline import extract_from_url, extract_from_text
from .library import CardTemplate, get_all_templates, get_template, get_template_choices
from .normalize import normalize_issuer, simplify_card_name, get_display_name, match_to_library_template
from .periods import (
    get_current_period,
    get_period_display_name,
    is_credit_used_this_period,
    is_reminder_snoozed,
    get_unused_credits_count,
    mark_credit_used,
    mark_credit_unused,
    snooze_credit_reminder,
    unsnooze_credit_reminder,
    snooze_all_reminders,
)

__all__ = [
    # Models
    "Card",
    "SignupBonus",
    "Credit",
    "CardData",
    "CardTemplate",
    "CreditUsage",
    # Storage
    "CardStorage",
    # Extraction pipeline (main API)
    "extract_from_url",
    "extract_from_text",
    # Card library
    "get_all_templates",
    "get_template",
    "get_template_choices",
    # Normalization
    "normalize_issuer",
    "simplify_card_name",
    "get_display_name",
    "match_to_library_template",
    # Period/benefit tracking
    "get_current_period",
    "get_period_display_name",
    "is_credit_used_this_period",
    "is_reminder_snoozed",
    "get_unused_credits_count",
    "mark_credit_used",
    "mark_credit_unused",
    "snooze_credit_reminder",
    "unsnooze_credit_reminder",
    "snooze_all_reminders",
    # Utilities
    "fetch_card_page",
    "get_allowed_domains",
    "preprocess_text",
    "get_char_reduction",
]
