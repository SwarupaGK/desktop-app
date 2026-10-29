"""
db_lc.py
Handles LC generation tracking.
Call `ensure_lc_column()` once at app startup (add to your main db init).
"""

import sqlite3

from config import DB_PATH


def ensure_lc_column():
    """Add lc_count column to students table if it doesn't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE students ADD COLUMN lc_count INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists — fine
    finally:
        conn.close()


def get_lc_count(student_db_id: int) -> int:
    """Return how many LCs have been generated for this student."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT lc_count FROM students WHERE id = ?", (student_db_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0


def increment_lc_count(student_db_id: int) -> int:
    """Increment LC count and return the NEW count."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE students SET lc_count = COALESCE(lc_count, 0) + 1 WHERE id = ?",
        (student_db_id,)
    )
    conn.commit()
    cur.execute("SELECT lc_count FROM students WHERE id = ?", (student_db_id,))
    new_count = cur.fetchone()[0]
    conn.close()
    return new_count
