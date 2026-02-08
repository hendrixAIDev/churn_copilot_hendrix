"""AI extraction rate limiting for cost control.

Tracks AI extraction usage per user with daily and monthly limits.
Also tracks global usage across all users for budget protection.

Free tier limits:
- 2 AI extractions per user per day
- 10 AI extractions per user per month
- 500 total extractions globally per month (budget protection)
"""

from datetime import datetime, date
from uuid import UUID, uuid4
from typing import Tuple, Optional, Dict, Any

from .database import get_cursor


# Free tier limits
FREE_TIER_DAILY_LIMIT = 2
FREE_TIER_MONTHLY_LIMIT = 10
GLOBAL_MONTHLY_LIMIT = 500  # Budget protection


def get_current_month_key() -> str:
    """Get the current month key (YYYY-MM format)."""
    now = datetime.now()
    return f"{now.year:04d}-{now.month:02d}"


def get_current_day_key() -> str:
    """Get the current day key (YYYY-MM-DD format)."""
    now = datetime.now()
    return f"{now.year:04d}-{now.month:02d}-{now.day:02d}"


def get_extraction_count(user_id: UUID) -> Dict[str, int]:
    """Get daily and monthly extraction counts for user.
    
    Returns:
        Dict with 'daily' and 'monthly' counts
    """
    month_key = get_current_month_key()
    day_key = get_current_day_key()
    
    with get_cursor(commit=False) as cursor:
        # Get monthly count
        cursor.execute(
            """
            SELECT COALESCE(SUM(extraction_count), 0) as monthly_count
            FROM ai_extractions
            WHERE user_id = %s AND month_key = %s
            """,
            (str(user_id), month_key)
        )
        monthly = cursor.fetchone()['monthly_count']
        
        # Get daily count
        cursor.execute(
            """
            SELECT COALESCE(extraction_count, 0) as daily_count
            FROM ai_extractions
            WHERE user_id = %s AND day_key = %s
            """,
            (str(user_id), day_key)
        )
        result = cursor.fetchone()
        daily = result['daily_count'] if result else 0
        
    return {'daily': daily, 'monthly': monthly}


def get_global_monthly_count() -> int:
    """Get total extractions across all users this month."""
    month_key = get_current_month_key()
    
    with get_cursor(commit=False) as cursor:
        cursor.execute(
            """
            SELECT COALESCE(SUM(extraction_count), 0) as total
            FROM ai_extractions
            WHERE month_key = %s
            """,
            (month_key,)
        )
        result = cursor.fetchone()
        return result['total'] if result else 0


def check_extraction_limit(user_id: UUID) -> Tuple[bool, int, str]:
    """Check if user can perform another AI extraction.
    
    Checks daily, monthly, and global limits.
    
    Returns:
        Tuple of (can_extract, remaining_today, message)
    """
    counts = get_extraction_count(user_id)
    global_count = get_global_monthly_count()
    
    daily_remaining = FREE_TIER_DAILY_LIMIT - counts['daily']
    monthly_remaining = FREE_TIER_MONTHLY_LIMIT - counts['monthly']
    global_remaining = GLOBAL_MONTHLY_LIMIT - global_count
    
    # Check global limit first (budget protection)
    if global_remaining <= 0:
        return False, 0, (
            "AI extraction is temporarily unavailable due to high demand. "
            "Please try again next month or add cards manually from our library."
        )
    
    # Check daily limit
    if daily_remaining <= 0:
        return False, 0, (
            f"You've used your {FREE_TIER_DAILY_LIMIT} daily AI extractions. "
            f"Try again tomorrow, or add cards from our library. "
            f"({counts['monthly']}/{FREE_TIER_MONTHLY_LIMIT} used this month)"
        )
    
    # Check monthly limit
    if monthly_remaining <= 0:
        from datetime import datetime
        now = datetime.now()
        next_month = (now.month % 12) + 1
        next_year = now.year if next_month > now.month else now.year + 1
        return False, 0, (
            f"You've used all {FREE_TIER_MONTHLY_LIMIT} AI extractions this month. "
            f"Resets on {next_month}/1/{next_year}. "
            "You can still add cards from our library or enter details manually."
        )
    
    # User can extract
    effective_remaining = min(daily_remaining, monthly_remaining)
    return True, effective_remaining, (
        f"{effective_remaining} extraction{'s' if effective_remaining != 1 else ''} remaining today "
        f"({counts['monthly']}/{FREE_TIER_MONTHLY_LIMIT} used this month)"
    )


def get_usage_display(user_id: UUID) -> Dict[str, Any]:
    """Get usage info for display in UI.
    
    Returns:
        Dict with daily_used, daily_limit, monthly_used, monthly_limit
    """
    counts = get_extraction_count(user_id)
    return {
        'daily_used': counts['daily'],
        'daily_limit': FREE_TIER_DAILY_LIMIT,
        'daily_remaining': FREE_TIER_DAILY_LIMIT - counts['daily'],
        'monthly_used': counts['monthly'],
        'monthly_limit': FREE_TIER_MONTHLY_LIMIT,
        'monthly_remaining': FREE_TIER_MONTHLY_LIMIT - counts['monthly'],
    }


def record_extraction(
    user_id: UUID,
    input_tokens: int = 0,
    output_tokens: int = 0,
    model: str = "",
    extraction_type: str = "url",
    success: bool = True
) -> str:
    """Record an AI extraction with token usage.
    
    Args:
        user_id: User's UUID
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens used
        model: Model used (e.g., "gemini-2.5-flash", "claude-sonnet-4")
        extraction_type: Type of extraction ("url", "xlsx")
        success: Whether extraction succeeded
        
    Returns:
        Extraction ID for reference
    """
    month_key = get_current_month_key()
    day_key = get_current_day_key()
    extraction_id = str(uuid4())[:8]  # Short ID for reference
    
    with get_cursor() as cursor:
        # Update daily/monthly count
        cursor.execute(
            """
            INSERT INTO ai_extractions (user_id, month_key, day_key, extraction_count, last_extracted_at)
            VALUES (%s, %s, %s, 1, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, day_key)
            DO UPDATE SET
                extraction_count = ai_extractions.extraction_count + 1,
                last_extracted_at = CURRENT_TIMESTAMP
            """,
            (str(user_id), month_key, day_key)
        )
        
        # Log detailed usage for analysis (no PII)
        cursor.execute(
            """
            INSERT INTO ai_extraction_logs (
                extraction_id, user_id, month_key, day_key,
                input_tokens, output_tokens, model, extraction_type,
                success, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (extraction_id, str(user_id), month_key, day_key,
             input_tokens, output_tokens, model, extraction_type, success)
        )
    
    return extraction_id


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
            SELECT month_key, SUM(extraction_count) as extraction_count, 
                   MAX(last_extracted_at) as last_extracted_at
            FROM ai_extractions
            WHERE user_id = %s
            GROUP BY month_key
            ORDER BY month_key DESC
            LIMIT %s
            """,
            (str(user_id), months)
        )
        return cursor.fetchall()


def get_usage_analytics(month_key: Optional[str] = None) -> Dict[str, Any]:
    """Get usage analytics for monitoring (no PII).
    
    Args:
        month_key: Month to analyze (defaults to current)
        
    Returns:
        Dict with total_extractions, unique_users, by_model, by_type
    """
    if not month_key:
        month_key = get_current_month_key()
    
    with get_cursor(commit=False) as cursor:
        # Total extractions and unique users
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_extractions,
                COUNT(DISTINCT user_id) as unique_users,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens
            FROM ai_extraction_logs
            WHERE month_key = %s
            """,
            (month_key,)
        )
        totals = cursor.fetchone()
        
        # By model
        cursor.execute(
            """
            SELECT model, COUNT(*) as count, SUM(input_tokens + output_tokens) as tokens
            FROM ai_extraction_logs
            WHERE month_key = %s
            GROUP BY model
            """,
            (month_key,)
        )
        by_model = cursor.fetchall()
        
        # By type
        cursor.execute(
            """
            SELECT extraction_type, COUNT(*) as count
            FROM ai_extraction_logs
            WHERE month_key = %s
            GROUP BY extraction_type
            """,
            (month_key,)
        )
        by_type = cursor.fetchall()
        
    return {
        'month': month_key,
        'total_extractions': totals['total_extractions'] if totals else 0,
        'unique_users': totals['unique_users'] if totals else 0,
        'total_input_tokens': totals['total_input_tokens'] if totals else 0,
        'total_output_tokens': totals['total_output_tokens'] if totals else 0,
        'by_model': by_model or [],
        'by_type': by_type or [],
        'global_limit': GLOBAL_MONTHLY_LIMIT,
        'global_remaining': GLOBAL_MONTHLY_LIMIT - (totals['total_extractions'] if totals else 0),
    }
