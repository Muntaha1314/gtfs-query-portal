"""
Connecting the database
Done!

"""

import os
import psycopg2
import psycopg2.extras
import logging

from typing import Optional, List, Dict, Any
from configuration import load_config

logger = logging.getLogger(__name__)


def connect_Database():
    conn = None
    cur = None

    try: 
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "gtfs_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            client_encoding='UTF8'
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        logger.info("Successfully connected to the database.")

    except Exception as e:
        logger.error("An error occurred while connecting to the database: %s", e)
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()


def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    conn = None
    cur = None
    results = []

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "gtfs_portals"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            client_encoding='UTF8'
        )
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(query, params)
        results = [dict(row) for row in cur.fetchall()]
        logger.info("Query executed successfully.")

    except Exception as e:
        logger.exception("An error occurred while executing the query")
        raise

    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return results

if __name__ == '__main__':
    load_config()
    connect_Database()

def test_database_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "gtfs_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            client_encoding='UTF8'
        )
        cur = conn.cursor()
        cur.execute('SELECT version()')
        db_version = cur.fetchone()
        logger.info("Database version: %s", db_version)
    except Exception as e:
        logger.error("An error occurred while connecting to the database: %s", e)
        raise
    finally:
        if conn is not None:
            conn.close()


def execute_scalar_query(query: str, params: Optional[tuple] = None) -> Any:
    conn = None
    cur = None
    result = None

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "gtfs_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            client_encoding='UTF8'
        )
        cur = conn.cursor()
        cur.execute(query, params or ())
        result = cur.fetchone()[0]
        logger.info("Scalar query executed successfully.")

    except Exception as e:
        logger.error("An error occurred while executing the scalar query: %s", e)
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()

    return result


def update_insert_delete_query(query: str, params: Optional[tuple] = None) -> None:
    conn = None
    cur = None

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "gtfs_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
            client_encoding='UTF8'
        )
        cur = conn.cursor()
        cur.execute(query, params or ())
        conn.commit()
        logger.info("Update/Insert/Delete query executed successfully.")

    except Exception as e:
        logger.error("An error occurred while executing the update/insert/delete query: %s", e)
        if conn is not None:
            conn.rollback()
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()

