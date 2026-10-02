import psycopg2
try:
    from core.config import DB_CONFIG
except ImportError:
    from config import DB_CONFIG


def get_connection():
    """
    Create and return a PostgreSQL connection.
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
    Execute insert/update queries safely.
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
    Execute select queries safely.
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
