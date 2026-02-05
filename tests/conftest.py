"""Pytest configuration for ChurnPilot tests.

This file is automatically loaded by pytest before running any tests.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the app directory (parent of tests)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Ensure DATABASE_URL is set for all tests
if not os.getenv("DATABASE_URL"):
    raise ValueError("DATABASE_URL not found in .env file. Tests require database connection.")
