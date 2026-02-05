#!/usr/bin/env python3
"""Create feedback table in Supabase database."""

import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# SQL to create the feedback table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS churnpilot_feedback (
    id SERIAL PRIMARY KEY,
    user_email TEXT,
    feedback_type TEXT NOT NULL DEFAULT 'general',  -- 'bug', 'feature', 'general'
    message TEXT NOT NULL,
    page TEXT,  -- which tab/page they were on
    user_agent TEXT,  -- browser info
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_churnpilot_feedback_created ON churnpilot_feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_churnpilot_feedback_type ON churnpilot_feedback(feedback_type);
"""

def main():
    """Create the feedback table."""
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return False
    
    try:
        # Connect to database
        print(f"🔌 Connecting to database...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Execute SQL
        print("📝 Creating churnpilot_feedback table...")
        cursor.execute(CREATE_TABLE_SQL)
        conn.commit()
        
        # Verify table was created
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'churnpilot_feedback'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        print("\n✅ Table created successfully!")
        print("\nColumns:")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
