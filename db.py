"""
Database connection management for PostgreSQL with PostGIS and pgRouting
Uses environment variables for credentials
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Database configuration from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "gtfs_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Mendil")
DB_PORT = os.getenv("DB_PORT", "5432")

print("DB PASSWORD:", DB_PASSWORD)

def get_connection():
    """
    Create a new database connection
    
    Returns:
        psycopg2 connection object
        
    Raises:
        psycopg2.Error: If connection fails
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise


@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for database queries with automatic cursor cleanup
    
    Args:
        commit (bool): Whether to commit changes (for INSERT/UPDATE/DELETE)
        
    Yields:
        RealDictCursor: Dictionary-based cursor for easy row access
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        if commit:
            conn.commit()
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def test_database_connection() -> bool:
    """
    Test database connection
    
    Returns:
        bool: True if connection successful
        
    Raises:
        Exception: If connection fails
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        raise Exception(f"Database connection test failed: {e}")


def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """
    Execute a SELECT query and return results as list of dictionaries
    
    Args:
        query (str): SQL query string
        params (tuple): Query parameters for safe SQL execution
        
    Returns:
        List[Dict]: Query results
    """
    with get_db_cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()


def execute_query_one(query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
    """
    Execute a SELECT query and return first result as dictionary
    
    Args:
        query (str): SQL query string
        params (tuple): Query parameters for safe SQL execution
        
    Returns:
        Dict or None: First row or None if no results
    """
    with get_db_cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()


def execute_query_scalar(query: str, params: tuple = None) -> Any:
    """
    Execute a query and return a single scalar value
    
    Args:
        query (str): SQL query string
        params (tuple): Query parameters for safe SQL execution
        
    Returns:
        Any: Single scalar value
    """
    result = execute_query_one(query, params)
    if result:
        return list(result.values())[0]
    return None
