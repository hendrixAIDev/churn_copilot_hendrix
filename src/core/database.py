"""Database connection and schema management for ChurnPilot."""

import os
import logging
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """Get database URL from environment variables or Streamlit secrets.

    Checks environment variables first (platform-independent),
    then falls back to st.secrets if available (Streamlit deployment).

    Returns:
        PostgreSQL connection URL.

    Raises:
        ValueError: If DATABASE_URL is not set.
    """
    # Try environment variable first (platform-independent)
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    
    # Fall back to Streamlit secrets (if Streamlit is available)
    try:
        import streamlit as st
        url = st.secrets.get("DATABASE_URL")
        if url:
            return url
    except Exception:
        pass

    raise ValueError(
        "DATABASE_URL not found. "
        "Set it as an environment variable or in Streamlit secrets."
    )


def get_schema_sql() -> str:
    """Get SQL schema for all tables.

    Returns:
        SQL string to create all tables.
    """
    return """
    -- Users table
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

    -- User sessions (for persistent login across page refresh)
    CREATE TABLE IF NOT EXISTS sessions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token VARCHAR(64) UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

    -- User preferences
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        sort_by VARCHAR(50) DEFAULT 'date_added',
        sort_descending BOOLEAN DEFAULT TRUE,
        group_by_issuer BOOLEAN DEFAULT FALSE,
        auto_enrich_enabled BOOLEAN DEFAULT TRUE,
        enrichment_min_confidence FLOAT DEFAULT 0.7,
        onboarding_completed BOOLEAN DEFAULT FALSE,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Cards
    CREATE TABLE IF NOT EXISTS cards (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        nickname VARCHAR(255),
        issuer VARCHAR(100) NOT NULL,
        annual_fee INTEGER DEFAULT 0,
        opened_date DATE,
        annual_fee_date DATE,
        closed_date DATE,
        is_business BOOLEAN DEFAULT FALSE,
        notes TEXT,
        raw_text TEXT,
        template_id VARCHAR(100),
        benefits_reminder_snoozed_until DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_cards_user_id ON cards(user_id);
    CREATE INDEX IF NOT EXISTS idx_cards_issuer ON cards(issuer);

    -- Signup bonuses (one per card)
    CREATE TABLE IF NOT EXISTS signup_bonuses (
        card_id UUID PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE,
        points_or_cash VARCHAR(100) NOT NULL,
        spend_requirement FLOAT NOT NULL,
        time_period_days INTEGER NOT NULL,
        deadline DATE,
        spend_progress FLOAT DEFAULT 0,
        achieved BOOLEAN DEFAULT FALSE
    );

    -- Card credits/perks
    CREATE TABLE IF NOT EXISTS card_credits (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        amount FLOAT NOT NULL,
        frequency VARCHAR(50) DEFAULT 'monthly',
        notes TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_card_credits_card_id ON card_credits(card_id);

    -- Credit usage tracking
    CREATE TABLE IF NOT EXISTS credit_usage (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
        credit_name VARCHAR(255) NOT NULL,
        last_used_period VARCHAR(20),
        reminder_snoozed_until DATE,
        UNIQUE(card_id, credit_name)
    );
    CREATE INDEX IF NOT EXISTS idx_credit_usage_card_id ON credit_usage(card_id);

    -- Retention offers
    CREATE TABLE IF NOT EXISTS retention_offers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
        date_called DATE NOT NULL,
        offer_details TEXT NOT NULL,
        accepted BOOLEAN NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_retention_offers_card_id ON retention_offers(card_id);

    -- Product changes
    CREATE TABLE IF NOT EXISTS product_changes (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
        date_changed DATE NOT NULL,
        from_product VARCHAR(255) NOT NULL,
        to_product VARCHAR(255) NOT NULL,
        reason TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_product_changes_card_id ON product_changes(card_id);

    -- AI extraction tracking (for cost control)
    CREATE TABLE IF NOT EXISTS ai_extractions (
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        month_key VARCHAR(7) NOT NULL,  -- Format: "YYYY-MM"
        extraction_count INTEGER DEFAULT 0,
        last_extracted_at TIMESTAMP,
        PRIMARY KEY (user_id, month_key)
    );
    CREATE INDEX IF NOT EXISTS idx_ai_extractions_user_id ON ai_extractions(user_id);
    CREATE INDEX IF NOT EXISTS idx_ai_extractions_month_key ON ai_extractions(month_key);
    """


@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Get a direct database connection.
    
    Creates a new connection for each request.
    Automatically closes the connection on exit.

    Yields:
        Database connection (auto-closed on exit).
        
    Raises:
        psycopg2.Error: If unable to connect to database.
    """
    conn = None
    try:
        conn = psycopg2.connect(get_database_url())
        yield conn
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")


@contextmanager
def get_cursor(commit: bool = True) -> Generator[RealDictCursor, None, None]:
    """Get a database cursor with dict results.

    Args:
        commit: Whether to commit on successful exit.

    Yields:
        Database cursor (auto-closed on exit).
    """
    with get_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()


def init_database() -> None:
    """Initialize database schema.

    Creates all tables if they don't exist.
    """
    with get_cursor() as cursor:
        cursor.execute(get_schema_sql())


def check_connection() -> bool:
    """Check if database connection works.

    Returns:
        True if connection successful.
    """
    try:
        with get_cursor(commit=False) as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception:
        return False


# Connection pooling removed due to Streamlit Cloud initialization issues
# Will be re-implemented with better compatibility later
