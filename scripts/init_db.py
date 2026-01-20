#!/usr/bin/env python3
"""Initialize the ChurnPilot database.

Usage:
    python scripts/init_db.py

Requires DATABASE_URL environment variable to be set.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

from src.core.database import init_database, check_connection, get_database_url


def main():
    """Initialize the database."""
    print("ChurnPilot Database Initialization")
    print("=" * 40)

    # Check DATABASE_URL is set
    try:
        url = get_database_url()
        # Hide password in output
        safe_url = url.split("@")[-1] if "@" in url else url
        print(f"Database: ...@{safe_url}")
    except ValueError as e:
        print(f"ERROR: {e}")
        print("\nSet DATABASE_URL in your .env file or environment.")
        sys.exit(1)

    # Test connection
    print("\nTesting connection...")
    if not check_connection():
        print("ERROR: Could not connect to database.")
        print("Check your DATABASE_URL and ensure the database server is running.")
        sys.exit(1)
    print("Connection successful!")

    # Initialize schema
    print("\nCreating tables...")
    try:
        init_database()
        print("Schema initialized successfully!")
    except Exception as e:
        print(f"ERROR: Failed to create tables: {e}")
        sys.exit(1)

    print("\n" + "=" * 40)
    print("Database ready!")


if __name__ == "__main__":
    main()
