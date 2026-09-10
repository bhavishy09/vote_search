"""
SQLite database storage and query manager for Voter List Search.
Stores parsed voter records, handles indexing, statistics, and caching.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "voters.db")


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables and indexes in voters.db."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # PDF files tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pdf_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                bhag_sankhya TEXT NOT NULL,
                total_voters INTEGER NOT NULL,
                file_size INTEGER DEFAULT 0,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Voters table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS voters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdf_filename TEXT NOT NULL,
                bhag_sankhya TEXT NOT NULL,
                kram_sankhya INTEGER NOT NULL,
                epic TEXT NOT NULL,
                name_hindi TEXT NOT NULL,
                name_english TEXT NOT NULL,
                relation_name_hindi TEXT DEFAULT '',
                relation_name_english TEXT DEFAULT '',
                relation_type TEXT DEFAULT 'Father',
                age INTEGER DEFAULT 0,
                gender TEXT DEFAULT '',
                house_number TEXT DEFAULT '',
                is_deleted INTEGER DEFAULT 0,
                search_key TEXT DEFAULT '',
                FOREIGN KEY(pdf_filename) REFERENCES pdf_files(filename) ON DELETE CASCADE
            )
            """
        )

        # Indexes for speed
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_voters_bhag ON voters(bhag_sankhya)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_voters_kram ON voters(kram_sankhya)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_voters_epic ON voters(epic)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_voters_name_en ON voters(name_english)")

        conn.commit()


def save_voters_batch(filename: str, bhag_sankhya: str, voters: List[Dict[str, Any]], file_size: int = 0) -> int:
    """
    Saves or replaces voter records for a given PDF file.
    Uses a transaction to insert all records efficiently.
    """
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()

        # Delete existing entries for this file if already ingested
        cursor.execute("DELETE FROM voters WHERE pdf_filename = ?", (filename,))
        cursor.execute("DELETE FROM pdf_files WHERE filename = ?", (filename,))

        # Register file
        cursor.execute(
            """
            INSERT INTO pdf_files (filename, bhag_sankhya, total_voters, file_size)
            VALUES (?, ?, ?, ?)
            """,
            (filename, bhag_sankhya, len(voters), file_size),
        )

        # Batch insert voters
        insert_sql = """
            INSERT INTO voters (
                pdf_filename, bhag_sankhya, kram_sankhya, epic,
                name_hindi, name_english, relation_name_hindi, relation_name_english,
                relation_type, age, gender, house_number, is_deleted, search_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        rows = [
            (
                filename,
                v.get("bhag_sankhya", bhag_sankhya),
                v.get("kram_sankhya", 0),
                v.get("epic", ""),
                v.get("name_hindi", ""),
                v.get("name_english", ""),
                v.get("relation_name_hindi", ""),
                v.get("relation_name_english", ""),
                v.get("relation_type", "Father"),
                v.get("age", 0),
                v.get("gender", ""),
                v.get("house_number", ""),
                1 if v.get("is_deleted") else 0,
                v.get("search_key", ""),
            )
            for v in voters
        ]

        cursor.executemany(insert_sql, rows)
        conn.commit()

    return len(voters)


def get_all_voters(bhag_sankhya: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves voter records (optionally filtered by Bhag Sankhya).
    Returns dictionaries.
    """
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        if bhag_sankhya and bhag_sankhya != "all":
            cursor.execute("SELECT * FROM voters WHERE bhag_sankhya = ? ORDER BY kram_sankhya", (bhag_sankhya,))
        else:
            cursor.execute("SELECT * FROM voters ORDER BY bhag_sankhya, kram_sankhya")

        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_db_stats() -> Dict[str, Any]:
    """Returns total voter counts, distinct part numbers, and files list."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM voters")
        total_voters = cursor.fetchone()[0]

        cursor.execute("SELECT DISTINCT bhag_sankhya FROM voters ORDER BY CAST(bhag_sankhya AS INTEGER)")
        parts = [r[0] for r in cursor.fetchall()]

        cursor.execute("SELECT filename, bhag_sankhya, total_voters, uploaded_at FROM pdf_files ORDER BY id")
        files = [dict(r) for r in cursor.fetchall()]

        return {
            "total_voters": total_voters,
            "parts": parts,
            "files": files,
        }
