import os
import sqlite3
from contextlib import contextmanager

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "secure_file_sharing.db")


def init_db():
    """Initialize the database and create tables"""
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

        conn.commit()


@contextmanager
def get_db_connection():
    """Provides a database connection with context management"""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query, params=None):
    """Execute a database query"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor


def fetch_one(query, params=None):
    """Fetch a single row from the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()


def fetch_all(query, params=None):
    """Fetch all rows from the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()


init_db()
