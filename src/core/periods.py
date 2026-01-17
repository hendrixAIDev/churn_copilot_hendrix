"""Period utilities for tracking credit/benefit usage.

This module provides functions to determine the current period
based on a credit's frequency, and to track usage across periods.
"""

from datetime import date

from .models import CreditUsage


def get_current_period(frequency: str, ref_date: date | None = None) -> str:
    """Get the current period identifier for a given frequency.

    Args:
        frequency: Credit frequency (monthly, quarterly, semi-annually, annual)
        ref_date: Reference date (defaults to today)

    Returns:
        Period identifier string:
        - monthly: "2024-01", "2024-02", etc.
        - quarterly: "2024-Q1", "2024-Q2", etc.
        - semi-annually: "2024-H1", "2024-H2"
        - annual: "2024"
    """
    if ref_date is None:
        ref_date = date.today()

    year = ref_date.year
    month = ref_date.month

    freq_lower = frequency.lower()

    if freq_lower == "monthly":
        return f"{year}-{month:02d}"
    elif freq_lower == "quarterly":
        quarter = (month - 1) // 3 + 1
        return f"{year}-Q{quarter}"
    elif freq_lower in ["semi-annually", "semi-annual"]:
        half = 1 if month <= 6 else 2
        return f"{year}-H{half}"
    elif freq_lower == "annual" or freq_lower == "annually":
        return str(year)
    else:
        # Unknown frequency - treat as annual
        return str(year)


def get_period_display_name(frequency: str, ref_date: date | None = None) -> str:
    """Get a human-readable name for the current period.

    Args:
        frequency: Credit frequency
        ref_date: Reference date (defaults to today)

    Returns:
        Human-readable period name (e.g., "January 2024", "Q1 2024", "H1 2024", "2024")
    """
    if ref_date is None:
        ref_date = date.today()

    year = ref_date.year
    month = ref_date.month

    freq_lower = frequency.lower()

    if freq_lower == "monthly":
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return f"{month_names[month - 1]} {year}"
    elif freq_lower == "quarterly":
        quarter = (month - 1) // 3 + 1
        return f"Q{quarter} {year}"
    elif freq_lower in ["semi-annually", "semi-annual"]:
        half = 1 if month <= 6 else 2
        return f"H{half} {year}"
    elif freq_lower == "annual" or freq_lower == "annually":
        return str(year)
    else:
        return str(year)


def is_credit_used_this_period(
    credit_name: str,
    frequency: str,
    credit_usage: dict[str, CreditUsage],
    ref_date: date | None = None,
) -> bool:
    """Check if a credit has been marked as used in the current period.

    Args:
        credit_name: Name of the credit
        frequency: Credit frequency
        credit_usage: Dictionary of credit usage data
        ref_date: Reference date (defaults to today)

    Returns:
        True if the credit was used this period, False otherwise
    """
    current_period = get_current_period(frequency, ref_date)
    usage = credit_usage.get(credit_name)

    if usage is None:
        return False

    return usage.last_used_period == current_period


def is_reminder_snoozed(
    credit_name: str,
    credit_usage: dict[str, CreditUsage],
    ref_date: date | None = None,
) -> bool:
    """Check if the reminder for a credit is currently snoozed.

    Args:
        credit_name: Name of the credit
        credit_usage: Dictionary of credit usage data
        ref_date: Reference date (defaults to today)

    Returns:
        True if the reminder is snoozed, False otherwise
    """
    if ref_date is None:
        ref_date = date.today()

    usage = credit_usage.get(credit_name)

    if usage is None or usage.reminder_snoozed_until is None:
        return False

    return ref_date < usage.reminder_snoozed_until


def get_unused_credits_count(
    credits: list,
    credit_usage: dict[str, CreditUsage],
    ref_date: date | None = None,
    include_snoozed: bool = False,
) -> int:
    """Count credits that haven't been used in their current period.

    Args:
        credits: List of Credit objects
        credit_usage: Dictionary of credit usage data
        ref_date: Reference date (defaults to today)
        include_snoozed: Whether to count snoozed credits

    Returns:
        Number of unused credits
    """
    count = 0
    for credit in credits:
        if not is_credit_used_this_period(credit.name, credit.frequency, credit_usage, ref_date):
            if include_snoozed or not is_reminder_snoozed(credit.name, credit_usage, ref_date):
                count += 1
    return count


def mark_credit_used(
    credit_name: str,
    frequency: str,
    credit_usage: dict[str, CreditUsage],
    ref_date: date | None = None,
) -> dict[str, CreditUsage]:
    """Mark a credit as used for the current period.

    Args:
        credit_name: Name of the credit
        frequency: Credit frequency
        credit_usage: Dictionary of credit usage data
        ref_date: Reference date (defaults to today)

    Returns:
        Updated credit_usage dictionary
    """
    current_period = get_current_period(frequency, ref_date)

    if credit_name not in credit_usage:
        credit_usage[credit_name] = CreditUsage()

    credit_usage[credit_name].last_used_period = current_period
    return credit_usage


def mark_credit_unused(
    credit_name: str,
    credit_usage: dict[str, CreditUsage],
) -> dict[str, CreditUsage]:
    """Mark a credit as unused (clear the used status).

    Args:
        credit_name: Name of the credit
        credit_usage: Dictionary of credit usage data

    Returns:
        Updated credit_usage dictionary
    """
    if credit_name in credit_usage:
        credit_usage[credit_name].last_used_period = None
    return credit_usage


def snooze_credit_reminder(
    credit_name: str,
    credit_usage: dict[str, CreditUsage],
    until_date: date,
) -> dict[str, CreditUsage]:
    """Snooze the reminder for a credit until a specific date.

    Args:
        credit_name: Name of the credit
        credit_usage: Dictionary of credit usage data
        until_date: Date until which to snooze

    Returns:
        Updated credit_usage dictionary
    """
    if credit_name not in credit_usage:
        credit_usage[credit_name] = CreditUsage()

    credit_usage[credit_name].reminder_snoozed_until = until_date
    return credit_usage


def unsnooze_credit_reminder(
    credit_name: str,
    credit_usage: dict[str, CreditUsage],
) -> dict[str, CreditUsage]:
    """Remove the snooze from a credit reminder.

    Args:
        credit_name: Name of the credit
        credit_usage: Dictionary of credit usage data

    Returns:
        Updated credit_usage dictionary
    """
    if credit_name in credit_usage:
        credit_usage[credit_name].reminder_snoozed_until = None
    return credit_usage


def snooze_all_reminders(
    credits: list,
    credit_usage: dict[str, CreditUsage],
    until_date: date,
) -> dict[str, CreditUsage]:
    """Snooze all credit reminders for a card.

    Args:
        credits: List of Credit objects
        credit_usage: Dictionary of credit usage data
        until_date: Date until which to snooze

    Returns:
        Updated credit_usage dictionary
    """
    for credit in credits:
        credit_usage = snooze_credit_reminder(credit.name, credit_usage, until_date)
    return credit_usage
