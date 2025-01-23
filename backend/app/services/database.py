import os
import sqlite3
from contextlib import contextmanager

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "secure_file_sharing.db")


def init_db():
    """
    Initialize the SQLite database and create necessary tables if they don't exist.

    Creates the following tables:
    - users: Stores user account information
    - files: Stores uploaded file metadata
    - file_shares: Stores file sharing information
    - mfa_codes: Stores MFA codes for users
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            mfa_enabled BOOLEAN DEFAULT 0
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            encrypted_key TEXT NOT NULL,
            encryption_salt TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS file_shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            shared_by INTEGER NOT NULL,
            shared_with INTEGER,
            permissions TEXT NOT NULL,
            token TEXT UNIQUE,
            expires_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (file_id) REFERENCES files (id),
            FOREIGN KEY (shared_by) REFERENCES users (id),
            FOREIGN KEY (shared_with) REFERENCES users (id)
        )
        """
        )

        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS mfa_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
        )

        conn.commit()


@contextmanager
def get_db_connection():
    """
    Create a database connection with context management.

    Yields:
        sqlite3.Connection: Database connection object

    Note:
        Connection is automatically closed when context exits
    """
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query, params=None):
    """
    Execute a database query with optional parameters.

    Args:
        query (str): SQL query to execute
        params (tuple, optional): Query parameters

    Returns:
        sqlite3.Cursor: Query cursor
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor


def fetch_one(query, params=None):
    """
    Execute a query and fetch a single row.

    Args:
        query (str): SQL query to execute
        params (tuple, optional): Query parameters

    Returns:
        tuple: Single row result or None if no results
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()


def fetch_all(query, params=None):
    """
    Execute a query and fetch all rows.

    Args:
        query (str): SQL query to execute
        params (tuple, optional): Query parameters

    Returns:
        List[tuple]: List of result rows
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()


init_db()
