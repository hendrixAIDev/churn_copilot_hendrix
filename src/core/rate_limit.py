"""Rate limiting for authentication and user actions.

Provides simple in-memory rate limiting to prevent abuse.
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple


# Rate limit storage (in-memory, module-level)
# Format: {key: {"count": int, "locked_until": datetime | None, "window_start": datetime}}
_login_attempts: Dict[str, Dict] = {}
_signup_attempts: Dict[str, Dict] = {}
_feedback_attempts: Dict[str, Dict] = {}

# Configuration
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15
MAX_SIGNUP_ATTEMPTS = 3
SIGNUP_WINDOW_HOURS = 1
MAX_FEEDBACK_ATTEMPTS = 5
FEEDBACK_WINDOW_HOURS = 1


def _get_or_create_record(storage: Dict, key: str) -> Dict:
    """Get or create a rate limit record.
    
    Args:
        storage: The storage dict to use.
        key: The key to look up.
        
    Returns:
        The rate limit record.
    """
    if key not in storage:
        storage[key] = {
            "count": 0,
            "locked_until": None,
            "window_start": datetime.utcnow()
        }
    return storage[key]


def _reset_if_window_expired(record: Dict, window_hours: float) -> None:
    """Reset counter if the time window has expired.
    
    Args:
        record: The rate limit record.
        window_hours: Size of the time window in hours.
    """
    window_duration = timedelta(hours=window_hours)
    if datetime.utcnow() - record["window_start"] > window_duration:
        record["count"] = 0
        record["window_start"] = datetime.utcnow()
        record["locked_until"] = None


def check_login_rate_limit(email: str) -> Tuple[bool, str]:
    """Check if login is allowed for this email.
    
    Args:
        email: Email address attempting to log in.
        
    Returns:
        Tuple of (allowed: bool, message: str).
        If not allowed, message contains user-friendly error.
    """
    email = email.lower().strip()
    record = _get_or_create_record(_login_attempts, email)
    
    # Check if currently locked out
    if record["locked_until"]:
        if datetime.utcnow() < record["locked_until"]:
            remaining = record["locked_until"] - datetime.utcnow()
            minutes = int(remaining.total_seconds() / 60) + 1
            return False, f"Too many login attempts. Please try again in {minutes} minute{'s' if minutes != 1 else ''}."
        else:
            # Lockout expired, reset
            record["count"] = 0
            record["locked_until"] = None
    
    # Check if limit reached
    if record["count"] >= MAX_LOGIN_ATTEMPTS:
        # Lock out
        record["locked_until"] = datetime.utcnow() + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
        return False, f"Too many login attempts. Please try again in {LOGIN_LOCKOUT_MINUTES} minutes."
    
    return True, ""


def record_login_failure(email: str) -> None:
    """Record a failed login attempt.
    
    Args:
        email: Email address that failed to log in.
    """
    email = email.lower().strip()
    record = _get_or_create_record(_login_attempts, email)
    record["count"] += 1


def reset_login_attempts(email: str) -> None:
    """Reset login attempts for an email (on successful login).
    
    Args:
        email: Email address that successfully logged in.
    """
    email = email.lower().strip()
    if email in _login_attempts:
        _login_attempts[email]["count"] = 0
        _login_attempts[email]["locked_until"] = None


def check_signup_rate_limit(session_id: str) -> Tuple[bool, str]:
    """Check if signup is allowed for this session.
    
    Args:
        session_id: Unique session identifier (use Streamlit session ID or IP if available).
        
    Returns:
        Tuple of (allowed: bool, message: str).
        If not allowed, message contains user-friendly error.
    """
    record = _get_or_create_record(_signup_attempts, session_id)
    _reset_if_window_expired(record, SIGNUP_WINDOW_HOURS)
    
    if record["count"] >= MAX_SIGNUP_ATTEMPTS:
        return False, f"Too many signup attempts. Please try again in {SIGNUP_WINDOW_HOURS} hour{'s' if SIGNUP_WINDOW_HOURS != 1 else ''}."
    
    return True, ""


def record_signup_attempt(session_id: str) -> None:
    """Record a signup attempt.
    
    Args:
        session_id: Unique session identifier.
    """
    record = _get_or_create_record(_signup_attempts, session_id)
    record["count"] += 1


def check_feedback_rate_limit(user_id: str) -> Tuple[bool, str]:
    """Check if feedback submission is allowed for this user.
    
    Args:
        user_id: User's UUID string.
        
    Returns:
        Tuple of (allowed: bool, message: str).
        If not allowed, message contains user-friendly error.
    """
    record = _get_or_create_record(_feedback_attempts, user_id)
    _reset_if_window_expired(record, FEEDBACK_WINDOW_HOURS)
    
    if record["count"] >= MAX_FEEDBACK_ATTEMPTS:
        return False, "You've submitted several feedbacks recently. Please wait before submitting more."
    
    return True, ""


def record_feedback_submission(user_id: str) -> None:
    """Record a feedback submission.
    
    Args:
        user_id: User's UUID string.
    """
    record = _get_or_create_record(_feedback_attempts, user_id)
    record["count"] += 1


def cleanup_old_records(max_age_hours: int = 24) -> None:
    """Clean up old rate limit records to prevent memory bloat.
    
    Call this periodically (e.g., once per hour) to remove stale records.
    
    Args:
        max_age_hours: Remove records older than this many hours.
    """
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    
    for storage in [_login_attempts, _signup_attempts, _feedback_attempts]:
        keys_to_delete = []
        for key, record in storage.items():
            # Delete if window_start is old and not currently locked
            if record["window_start"] < cutoff and not record["locked_until"]:
                keys_to_delete.append(key)
            # Delete if lockout expired long ago
            elif record["locked_until"] and record["locked_until"] < cutoff:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del storage[key]
