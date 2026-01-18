"""Core business logic - framework agnostic."""

from .models import Card, SignupBonus, Credit, CardData, CreditUsage, RetentionOffer, ProductChange
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
from .importer import SpreadsheetImporter, ParsedCard, import_from_csv
from .five_twenty_four import calculate_five_twenty_four_status, get_five_twenty_four_timeline
from .validation import (
    validate_opened_date,
    validate_annual_fee,
    validate_signup_bonus,
    validate_card_name,
    has_errors,
    has_warnings,
    get_error_messages,
    get_warning_messages,
    ValidationWarning,
    ValidationError,
)

__all__ = [
    # Models
    "Card",
    "SignupBonus",
    "Credit",
    "CardData",
    "CardTemplate",
    "CreditUsage",
    "RetentionOffer",
    "ProductChange",
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
    # Importer
    "SpreadsheetImporter",
    "ParsedCard",
    "import_from_csv",
    # 5/24 tracking
    "calculate_five_twenty_four_status",
    "get_five_twenty_four_timeline",
    # Validation
    "validate_opened_date",
    "validate_annual_fee",
    "validate_signup_bonus",
    "validate_card_name",
    "has_errors",
    "has_warnings",
    "get_error_messages",
    "get_warning_messages",
    "ValidationWarning",
    "ValidationError",
]
