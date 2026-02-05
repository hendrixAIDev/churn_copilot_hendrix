"""Database connection and schema management for ChurnPilot."""

import os
import logging
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import PoolError

from .db_pool import get_connection_pool

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
    """Get a database connection from the pool.
    
    Automatically returns the connection to the pool on exit.
    Handles pool exhaustion gracefully with retries and clear error messages.

    Yields:
        Database connection (auto-returned to pool on exit).
        
    Raises:
        PoolError: If unable to get connection from pool after retries.
    """
    pool = get_connection_pool(get_database_url())
    conn = None
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = pool.getconn()
            break
        except PoolError as e:
            retry_count += 1
            logger.warning(f"Pool exhausted (attempt {retry_count}/{max_retries}): {e}")
            if retry_count >= max_retries:
                logger.error("Failed to get connection from pool after retries")
                raise PoolError(
                    f"Connection pool exhausted. All {pool.maxconn} connections are in use. "
                    "This may indicate a connection leak or excessive concurrent usage."
                ) from e
            # Brief pause before retry (exponential backoff)
            import time
            time.sleep(0.1 * (2 ** retry_count))
    
    try:
        yield conn
    finally:
        if conn is not None:
            try:
                pool.putconn(conn)
            except Exception as e:
                logger.error(f"Error returning connection to pool: {e}")


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


def get_pool_health() -> dict:
    """Get connection pool health statistics.
    
    Returns:
        Dictionary with pool health information including:
        - connections_in_use: Number of connections currently in use
        - connections_available: Number of connections available
        - total_connections: Total connections in pool
        - minconn: Minimum connections configured
        - maxconn: Maximum connections configured
        - pool_exhausted: Boolean indicating if pool is at capacity
    """
    try:
        pool = get_connection_pool(get_database_url())
        from .db_pool import get_pool_stats
        stats = get_pool_stats(pool)
        
        # Add derived health metrics
        if "connections_in_use" in stats and "maxconn" in stats:
            stats["pool_exhausted"] = stats["connections_in_use"] >= stats["maxconn"]
            stats["utilization_percent"] = (
                (stats["connections_in_use"] / stats["maxconn"] * 100)
                if stats["maxconn"] > 0 else 0
            )
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get pool health: {e}")
        return {"error": str(e)}
