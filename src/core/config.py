"""Configuration settings for ChurnPilot.

Environment-based feature flags and settings.
"""

import os
from typing import Literal

# Ensure environment variables are loaded
from . import env_loader  # noqa: F401


# ==================== FEATURE FLAGS ====================

def get_bool_env(key: str, default: str = "false") -> bool:
    """Get boolean from environment variable.
    
    Args:
        key: Environment variable name
        default: Default value if not set ("true" or "false")
        
    Returns:
        Boolean value
    """
    return os.environ.get(key, default).lower() in ("true", "1", "yes")


# Database vs localStorage toggle
# When False (default): Use localStorage/sessionStorage (existing behavior)
# When True: Use PostgreSQL database for persistence
USE_DATABASE = get_bool_env("USE_DATABASE", "false")


# ==================== FREE TIER LIMITS ====================

# Free tier limits (per JJ's decisions)
FREE_TIER_CARD_LIMIT = 20  # cards
FREE_TIER_AI_EXTRACTIONS = 10  # AI extractions per month


# ==================== STORAGE MODE ====================

StorageMode = Literal["local", "database"]

def get_storage_mode() -> StorageMode:
    """Get the current storage mode based on USE_DATABASE flag.
    
    Returns:
        "database" if USE_DATABASE is True, else "local"
    """
    return "database" if USE_DATABASE else "local"
