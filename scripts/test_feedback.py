#!/usr/bin/env python3
"""Insert a test feedback record to verify the system works."""

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

def insert_test_feedback():
    """Insert a test feedback record."""
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return False
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Insert test record
        cursor.execute(
            """
            INSERT INTO churnpilot_feedback (user_email, feedback_type, message, page, user_agent)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                "test@example.com",
                "bug",
                "This is a test bug report to verify the feedback system is working correctly.",
                "Dashboard",
                "Mozilla/5.0 (Test Agent)"
            )
        )
        
        feedback_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ Test feedback inserted successfully!")
        print(f"   ID: {feedback_id}")
        print(f"   Type: Bug Report")
        print(f"   User: test@example.com")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error inserting test feedback: {e}")
        return False

if __name__ == "__main__":
    success = insert_test_feedback()
    exit(0 if success else 1)
