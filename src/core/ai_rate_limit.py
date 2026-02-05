"""AI extraction rate limiting for cost control.

Tracks AI extraction usage per user per month to prevent budget overruns.
Free tier: 10 AI extractions per user per month.
"""

from datetime import datetime, date
from uuid import UUID
from typing import Tuple, Optional

from .database import get_cursor


# Free tier limit
FREE_TIER_MONTHLY_LIMIT = 10


def get_current_month_key() -> str:
    """Get the current month key (YYYY-MM format).
    
    Returns:
        Month key string like "2026-02"
    """
    now = datetime.now()
    return f"{now.year:04d}-{now.month:02d}"


def get_extraction_count(user_id: UUID) -> int:
    """Get the number of AI extractions used by user this month.
    
    Args:
        user_id: User's UUID
        
    Returns:
        Number of extractions used this month (0 if no record exists)
    """
    month_key = get_current_month_key()
    
    with get_cursor(commit=False) as cursor:
        cursor.execute(
            """
            SELECT extraction_count
            FROM ai_extractions
            WHERE user_id = %s AND month_key = %s
            """,
            (str(user_id), month_key)
        )
        result = cursor.fetchone()
        
        if result:
            return result['extraction_count']
        return 0


def check_extraction_limit(user_id: UUID) -> Tuple[bool, int, str]:
    """Check if user can perform another AI extraction.
    
    Args:
        user_id: User's UUID
        
    Returns:
        Tuple of (can_extract, remaining, message)
        - can_extract: True if user has extractions remaining
        - remaining: Number of extractions remaining
        - message: Human-friendly message about status
    """
    current_count = get_extraction_count(user_id)
    remaining = FREE_TIER_MONTHLY_LIMIT - current_count
    
    if remaining > 0:
        return True, remaining, f"{remaining}/{FREE_TIER_MONTHLY_LIMIT} AI extractions remaining this month"
    else:
        return False, 0, (
            "You've used all your AI extractions this month. "
            "You can still add cards from our library or enter details manually."
        )


def record_extraction(user_id: UUID) -> None:
    """Record an AI extraction for the current month.
    
    Creates a new record if none exists for this month, or increments existing count.
    
    Args:
        user_id: User's UUID
    """
    month_key = get_current_month_key()
    
    with get_cursor() as cursor:
        # Use INSERT ... ON CONFLICT to handle both new and existing records
        cursor.execute(
            """
            INSERT INTO ai_extractions (user_id, month_key, extraction_count, last_extracted_at)
            VALUES (%s, %s, 1, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, month_key)
            DO UPDATE SET
                extraction_count = ai_extractions.extraction_count + 1,
                last_extracted_at = CURRENT_TIMESTAMP
            """,
            (str(user_id), month_key)
        )


def get_extraction_history(user_id: UUID, months: int = 3) -> list:
    """Get extraction history for user.
    
    Args:
        user_id: User's UUID
        months: Number of recent months to retrieve
        
    Returns:
        List of dicts with month_key, extraction_count, last_extracted_at
    """
    with get_cursor(commit=False) as cursor:
        cursor.execute(
            """
            SELECT month_key, extraction_count, last_extracted_at
            FROM ai_extractions
            WHERE user_id = %s
            ORDER BY month_key DESC
            LIMIT %s
            """,
            (str(user_id), months)
        )
        return cursor.fetchall()
