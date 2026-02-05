"""Database connection pooling for ChurnPilot.

Uses psycopg2's ThreadedConnectionPool with a module-level singleton
to maintain a persistent connection pool across Streamlit reruns.
"""

from psycopg2.pool import ThreadedConnectionPool, PoolError
from typing import Optional
import logging
import threading

logger = logging.getLogger(__name__)

# Module-level singleton for connection pool
_pool: Optional[ThreadedConnectionPool] = None
_pool_lock = threading.Lock()


def get_connection_pool(database_url: str, minconn: int = 1, maxconn: int = 5) -> Optional[ThreadedConnectionPool]:
    """Get or create a connection pool.
    
    Uses a module-level singleton pattern to persist the pool across reruns.
    Thread-safe and suitable for Streamlit Cloud's single-worker setup.
    
    Args:
        database_url: PostgreSQL connection URL.
        minconn: Minimum number of connections to maintain (default: 1).
        maxconn: Maximum number of connections allowed (default: 5).
    
    Returns:
        ThreadedConnectionPool instance, or None if creation fails.
    """
    global _pool
    
    # Return existing pool if available
    if _pool is not None:
        return _pool
    
    # Create new pool (thread-safe)
    with _pool_lock:
        # Double-check after acquiring lock
        if _pool is not None:
            return _pool
        
        try:
            logger.info(f"Creating connection pool (minconn={minconn}, maxconn={maxconn})")
            _pool = ThreadedConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                dsn=database_url
            )
            return _pool
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            return None


def get_pool_stats(pool: ThreadedConnectionPool) -> dict:
    """Get statistics about the connection pool.
    
    Args:
        pool: The connection pool.
    
    Returns:
        Dictionary with pool statistics.
    """
    try:
        # Note: psycopg2 ThreadedConnectionPool doesn't expose these directly,
        # but we can introspect the internal _used and _pool sets
        used = len(pool._used) if hasattr(pool, '_used') else 0
        available = len(pool._pool) if hasattr(pool, '_pool') else 0
        
        return {
            "connections_in_use": used,
            "connections_available": available,
            "total_connections": used + available,
            "minconn": pool.minconn,
            "maxconn": pool.maxconn,
        }
    except Exception as e:
        logger.warning(f"Failed to get pool stats: {e}")
        return {
            "error": str(e),
            "minconn": pool.minconn if hasattr(pool, 'minconn') else None,
            "maxconn": pool.maxconn if hasattr(pool, 'maxconn') else None,
        }


def close_pool(pool: Optional[ThreadedConnectionPool]) -> None:
    """Close all connections in the pool.
    
    This should only be called when shutting down the application.
    
    Args:
        pool: The connection pool to close.
    """
    if pool is not None:
        try:
            pool.closeall()
            logger.info("Connection pool closed")
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")
