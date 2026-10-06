"""
PostgreSQL connection helpers.

Each helper opens a fresh connection and always closes it, so callers never
leak connections. There is no connection pool; at the current write rate
(a few inserts per second) that is acceptable.
"""

import psycopg2

# Support both package-style imports (core.config) and legacy root imports (config)
try:
    from core.config import DB_CONFIG
except ImportError:
    from config import DB_CONFIG


def get_connection():
    """
    Create and return a PostgreSQL connection.

    connect_timeout=3 makes collectors fail fast instead of hanging
    when the database is down.
    """
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        connect_timeout=3
    )


def execute_query(query, values=None):
    """
    Execute an INSERT/UPDATE/DELETE in its own transaction.

    Values are passed separately (`%s` placeholders), so psycopg2 escapes
    them and they cannot inject SQL. On failure the transaction is rolled
    back and the error is re-raised to the caller.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Database Error in execute_query: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_query(query, values=None):
    """
    Execute a SELECT and return all rows as a list of tuples.

    Unlike execute_query, errors are printed and None is returned, so
    callers must check for None.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, values)
        return cursor.fetchall()
    except Exception as e:
        print(f"Database Error in fetch_query: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
