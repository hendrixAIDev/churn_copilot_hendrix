"""Input validation for card data.

Provides validation functions to catch common user errors before saving cards.
"""

from datetime import date
from typing import Literal


class ValidationWarning:
    """A non-blocking warning about potentially incorrect input."""

    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return self.message


class ValidationError:
    """A blocking error that prevents saving invalid data."""

    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return self.message


ValidationResult = Literal["ok"] | ValidationWarning | ValidationError


def validate_opened_date(opened_date: date | None, required: bool = False) -> ValidationResult:
    """Validate card opened date.

    Args:
        opened_date: The date the card was opened.
        required: If True, missing date is a warning (not error, since user can set later).

    Returns:
        ValidationResult indicating if date is valid.
    """
    if opened_date is None:
        if required:
            return ValidationWarning(
                "No opened date provided. Without it, 5/24 tracking and "
                "SUB deadlines won't work correctly. You can add it later by editing the card."
            )
        return "ok"

    today = date.today()

    # Error: Date in the future
    if opened_date > today:
        return ValidationError(
            f"Opened date ({opened_date}) is in the future. "
            f"Please check the date - cards can't be opened before today."
        )

    # Warning: Very old date (likely a typo)
    from datetime import timedelta
    if opened_date < (today - timedelta(days=365 * 20)):
        return ValidationWarning(
            f"Opened date is over 20 years ago ({opened_date}). "
            f"Is this correct?"
        )

    return "ok"


def validate_annual_fee(annual_fee: int | float) -> ValidationResult:
    """Validate annual fee amount.

    Args:
        annual_fee: The annual fee in dollars.

    Returns:
        ValidationResult indicating if fee is valid.
    """
    # Error: Negative fee
    if annual_fee < 0:
        return ValidationError(
            f"Annual fee cannot be negative (${annual_fee}). "
            f"Enter 0 for no annual fee cards."
        )

    # Warning: Unusually high fee (likely a typo)
    if annual_fee > 1000:
        return ValidationWarning(
            f"Annual fee is unusually high (${annual_fee}). "
            f"Is this correct? Most cards have fees under $1000."
        )

    return "ok"


def validate_signup_bonus(
    bonus_amount: str | None,
    spend_requirement: float | int,
    time_period_days: int,
    opened_date: date | None,
) -> ValidationResult:
    """Validate signup bonus requirements.

    Args:
        bonus_amount: The bonus amount string (e.g., "60,000 points").
        spend_requirement: Required spend in dollars.
        time_period_days: Days to meet requirement.
        opened_date: When the card was opened.

    Returns:
        ValidationResult indicating if SUB is valid.
    """
    # If no bonus entered, nothing to validate
    if not bonus_amount:
        return "ok"

    # Warning: SUB entered but spend requirement is 0
    if spend_requirement <= 0:
        return ValidationWarning(
            "Signup bonus entered but spend requirement is $0. "
            "Most cards require spending to earn the bonus."
        )

    # Warning: SUB entered but time period is 0
    if time_period_days <= 0:
        return ValidationWarning(
            "Signup bonus entered but time period is 0 days. "
            "Typical periods are 90-120 days."
        )

    # Warning: SUB entered but no opened date (can't calculate deadline)
    if opened_date is None:
        return ValidationWarning(
            "Signup bonus deadline can't be calculated without an opened date. "
            "Consider adding the opened date to track your deadline."
        )

    # Warning: Very high spend requirement (likely a typo)
    if spend_requirement > 50000:
        return ValidationWarning(
            f"Spend requirement is very high (${spend_requirement:,.0f}). "
            f"Is this correct? Most cards require under $15,000."
        )

    # Warning: Very short time period
    if time_period_days < 30:
        return ValidationWarning(
            f"Time period is very short ({time_period_days} days). "
            f"Most cards give 90+ days to meet spend."
        )

    return "ok"


def validate_card_name(name: str, existing_names: list[str]) -> ValidationResult:
    """Validate card name for duplicates.

    Args:
        name: The card name to validate.
        existing_names: List of existing card names in the system.

    Returns:
        ValidationResult indicating if name is valid.
    """
    if not name or not name.strip():
        return ValidationError("Card name cannot be empty.")

    # Warning: Duplicate name (might be intentional for multiple instances)
    if name in existing_names:
        return ValidationWarning(
            f"You already have a card named '{name}'. "
            f"Consider using a nickname to distinguish them (e.g., 'P2's card')."
        )

    return "ok"


def has_errors(results: list[ValidationResult]) -> bool:
    """Check if any validation results contain errors.

    Args:
        results: List of validation results.

    Returns:
        True if any result is a ValidationError, False otherwise.
    """
    return any(isinstance(r, ValidationError) for r in results)


def has_warnings(results: list[ValidationResult]) -> bool:
    """Check if any validation results contain warnings.

    Args:
        results: List of validation results.

    Returns:
        True if any result is a ValidationWarning, False otherwise.
    """
    return any(isinstance(r, ValidationWarning) for r in results)


def get_error_messages(results: list[ValidationResult]) -> list[str]:
    """Extract error messages from validation results.

    Args:
        results: List of validation results.

    Returns:
        List of error message strings.
    """
    return [str(r) for r in results if isinstance(r, ValidationError)]


def get_warning_messages(results: list[ValidationResult]) -> list[str]:
    """Extract warning messages from validation results.

    Args:
        results: List of validation results.

    Returns:
        List of warning message strings.
    """
    return [str(r) for r in results if isinstance(r, ValidationWarning)]
