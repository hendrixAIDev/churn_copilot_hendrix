"""Environment variable loader - must be imported first!

This module ensures .env.local (for local dev) is loaded before .env (for deployment).
Import this at the top of any module that needs environment variables.
"""

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables ONCE at module import
_ENV_LOADED = False

if not _ENV_LOADED:
    project_root = Path(__file__).parent.parent.parent
    
    # Prefer .env.local (local development) over .env (deployment/default)
    if (project_root / ".env.local").exists():
        load_dotenv(project_root / ".env.local", override=True)
    elif (project_root / ".env").exists():
        load_dotenv(project_root / ".env")
    
    _ENV_LOADED = True
