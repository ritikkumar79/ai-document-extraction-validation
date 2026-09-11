"""Database connection helpers.

Supports SQLite for zero-config local development and PostgreSQL for deployed
persistent storage (for example Supabase or a managed Render PostgreSQL DB).
"""

import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.core.config import DATABASE_URL


def _is_postgres() -> bool:
    return DATABASE_URL.startswith(("postgres://", "postgresql://"))


def _sqlite_path() -> Path:
    if DATABASE_URL.startswith("sqlite:///"):
        return Path(DATABASE_URL.replace("sqlite:///", "", 1))
    return Path("documents.db")


DB_PATH = _sqlite_path()
if not _is_postgres():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> Any:
    """Return a database connection with dict-like rows."""
    if _is_postgres():
        import psycopg
        from psycopg.rows import dict_row

        # Supabase commonly supplies postgres://; psycopg accepts postgresql://.
        database_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return psycopg.connect(database_url, row_factory=dict_row, connect_timeout=10)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the documents table if it does not already exist."""
    if _is_postgres():
        sql = """
        CREATE TABLE IF NOT EXISTS documents (
            id BIGSERIAL PRIMARY KEY,
            document_name TEXT NOT NULL UNIQUE,
            document_type TEXT NOT NULL,
            processing_status TEXT NOT NULL,
            result_json TEXT NOT NULL,
            processed_at TEXT NOT NULL,
            processing_time_ms INTEGER NOT NULL
        )
        """
    else:
        sql = """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_name TEXT NOT NULL UNIQUE,
            document_type TEXT NOT NULL,
            processing_status TEXT NOT NULL,
            result_json TEXT NOT NULL,
            processed_at TEXT NOT NULL,
            processing_time_ms INTEGER NOT NULL
        )
        """

    with get_connection() as conn:
        conn.execute(sql)
        conn.commit()
