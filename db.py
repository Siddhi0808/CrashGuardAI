import psycopg2
from config import DB_CONFIG


def get_connection():
    """
    Create and return a PostgreSQL connection
    """
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )
    return conn


def execute_query(query, values=None):
    """
    Execute insert/update queries
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query, values)
        conn.commit()
    except Exception as e:
        print("Database Error:", e)
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def fetch_query(query, values=None):
    """
    Execute select queries
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query, values)
        result = cursor.fetchall()
        return result
    except Exception as e:
        print("Database Error:", e)
        return None
    finally:
        cursor.close()
        conn.close()
