import sqlite3
from contextlib import contextmanager
import os

from config import DB_PATH, ensure_data_file

@contextmanager
def get_db_connection(row_factory=False):
    """Context manager to handle DB connections safely."""
    try:
        conn = sqlite3.connect(DB_PATH)
        if row_factory:
            conn.row_factory = sqlite3.Row
        # Test database connection
        conn.execute("SELECT 1")
        yield conn
    except sqlite3.Error as e:
        # Create database if it doesn't exist (for .exe files)
        init_db()
        conn = sqlite3.connect(DB_PATH)
        if row_factory:
            conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if 'conn' in locals():
            conn.close()

def init_db():
    """Create database table with all required fields."""
    ensure_data_file("students.db")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    
    # Ensure database is properly initialized for .exe files
    try:
        cur.execute("SELECT 1 FROM students LIMIT 1")
    except sqlite3.OperationalError:
        # Database exists but may be corrupted, recreate
        cur.execute("DROP TABLE IF EXISTS students")
        cur.execute("DROP TABLE IF EXISTS academic_years")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id            TEXT UNIQUE,
            aadhaar               TEXT,
            pen_number            TEXT,
            name_mr               TEXT,
            mother_name_mr        TEXT,
            caste                 TEXT,
            subcaste              TEXT,
            religion              TEXT,
            birth_place           TEXT,
            birth_taluka          TEXT,
            birth_dist            TEXT,
            birth_date_num        TEXT,
            birth_date_words      TEXT,
            previous_school       TEXT,
            admission_date        TEXT,
            current_class         TEXT,
            progress              TEXT,
            behaviour             TEXT,
            leaving_date          TEXT,
            class_at_leaving      TEXT,
            leaving_reason        TEXT,
            remark                TEXT,
            lc_no                 INTEGER,
            lc_count              INTEGER DEFAULT 0,
            bonafide_count        INTEGER DEFAULT 0,
            academic_year         TEXT,
            student_status        TEXT DEFAULT 'current',
            passout_year          TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS academic_years (
            academic_year TEXT PRIMARY KEY,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    _migrate_db(conn)
    conn.close()


def _migrate_db(conn):
    """Safely add any missing columns to existing databases."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(students)")
    existing = {row[1] for row in cur.fetchall()}

    required = {
        "student_id":       "TEXT",
        "aadhaar":          "TEXT",
        "pen_number":       "TEXT",
        "name_mr":          "TEXT",
        "mother_name_mr":   "TEXT",
        "caste":            "TEXT",
        "subcaste":         "TEXT",
        "religion":         "TEXT",
        "birth_place":      "TEXT",
        "birth_taluka":     "TEXT",
        "birth_dist":       "TEXT",
        "birth_date_num":   "TEXT",
        "birth_date_words": "TEXT",
        "previous_school":  "TEXT",
        "admission_date":   "TEXT",
        "current_class":    "TEXT",
        "progress":         "TEXT",
        "behaviour":        "TEXT",
        "leaving_date":     "TEXT",
        "class_at_leaving": "TEXT",
        "leaving_reason":   "TEXT",
        "remark":           "TEXT",
        "lc_no":            "INTEGER",
        "lc_count":         "INTEGER DEFAULT 0",
        "bonafide_count":   "INTEGER DEFAULT 0",
        "academic_year":    "TEXT",
        "student_status":   "TEXT DEFAULT 'current'",
        "passout_year":     "TEXT",
        "residential_status":"TEXT DEFAULT 'निवासी'",
    }

    for col, col_type in required.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE students ADD COLUMN {col} {col_type}")
            print(f"[DB Migration] Added column: {col}")

    cur.execute(
        "SELECT id FROM students "
        "WHERE COALESCE(lc_count,0) > 0 AND lc_no IS NULL "
        "ORDER BY id"
    )
    rows_needing_lc_no = [row[0] for row in cur.fetchall()]
    for student_id in rows_needing_lc_no:
        cur.execute("SELECT COALESCE(MAX(lc_no), 0) + 1 FROM students")
        next_lc_no = cur.fetchone()[0] or 1
        cur.execute(
            "UPDATE students SET lc_no = ? WHERE id = ?",
            (next_lc_no, student_id),
        )

    # ── CRITICAL FIX: set student_status = 'current' for ALL old rows that have NULL ──
    cur.execute(
        "UPDATE students SET student_status = 'current' WHERE student_status IS NULL"
    )
    updated = cur.rowcount
    if updated > 0:
        print(f"[DB Migration] Fixed {updated} rows with NULL student_status → 'current'")

    cur.execute("""
        INSERT OR IGNORE INTO academic_years (academic_year)
        SELECT DISTINCT academic_year FROM students
        WHERE academic_year IS NOT NULL AND academic_year != ''
    """)

    conn.commit()
    print("[DB] Migration check complete.")


def save_student(data: dict) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("PRAGMA table_info(students)")
    valid_columns = {row[1] for row in cur.fetchall()}
    filtered     = {k: v for k, v in data.items() if k in valid_columns}
    if "id" not in filtered:
        filtered["id"] = _get_next_sequential_id(cur)
    columns      = ", ".join(filtered.keys())
    placeholders = ", ".join("?" for _ in filtered)
    values       = list(filtered.values())
    try:
        cur.execute(f"INSERT INTO students ({columns}) VALUES ({placeholders})", values)
        academic_year = (filtered.get("academic_year") or "").strip()
        if academic_year:
            cur.execute(
                "INSERT OR IGNORE INTO academic_years (academic_year) VALUES (?)",
                (academic_year,),
            )
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        print(f"[DB] Integrity Error: {e}")
        return False
    except Exception as e:
        print(f"[DB] Error: {e}")
        return False
    finally:
        conn.close()


def _get_next_sequential_id(cur) -> int:
    """Return the first available positive integer id."""
    cur.execute("SELECT id FROM students WHERE id IS NOT NULL ORDER BY id")
    rows = [row[0] for row in cur.fetchall()]

    expected = 1
    for existing_id in rows:
        if existing_id != expected:
            return expected
        expected += 1
    return expected


def get_all_students():
    """Fetch ALL students ordered by latest first."""
    with get_db_connection(row_factory=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM students ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]
        # The connection closes automatically when the 'with' block ends!



def get_current_students():
    """Fetch only students with student_status = 'current' (or NULL treated as current)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute(
        "SELECT * FROM students "
        "WHERE student_status = 'current' OR student_status IS NULL "
        "ORDER BY id DESC"
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_passout_students():
    """Fetch only students with student_status = 'passout'."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute(
        "SELECT * FROM students WHERE student_status = 'passout' ORDER BY id DESC"
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_students_by_academic_year(academic_year: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute(
        "SELECT * FROM students WHERE academic_year = ? ORDER BY id DESC",
        (academic_year,)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_academic_years():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        "SELECT academic_year FROM academic_years "
        "WHERE academic_year IS NOT NULL AND academic_year != '' "
        "UNION "
        "SELECT DISTINCT academic_year FROM students "
        "WHERE academic_year IS NOT NULL AND academic_year != '' "
        "ORDER BY academic_year DESC"
    )
    years = [row[0] for row in cur.fetchall()]
    conn.close()
    return years


def add_academic_year(academic_year):
    academic_year = (academic_year or "").strip()
    if not academic_year:
        return False
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT OR IGNORE INTO academic_years (academic_year) VALUES (?)",
            (academic_year,),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB] Error adding academic year: {e}")
        return False
    finally:
        conn.close()


def get_academic_year_stats(academic_year):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM students WHERE academic_year = ?", (academic_year,))
    total = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM students "
        "WHERE academic_year = ? AND (student_status = 'current' OR student_status IS NULL)",
        (academic_year,)
    )
    current = cur.fetchone()[0]
    conn.close()
    return {
        'total_students':   total,
        'current_students': current,
        'passout_students': total - current,
    }


def get_student_status(student_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute(
        "SELECT student_status FROM students WHERE student_id = ?", (student_id,)
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return 'Not Found'
    status = row['student_status']
    return 'Passout' if status == 'passout' else 'Current'


def update_student_status(student_id, leaving_date=None, leaving_reason=None):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    try:
        if leaving_date and leaving_reason:
            cur.execute("""
                UPDATE students
                SET leaving_date = ?, leaving_reason = ?, student_status = 'passout'
                WHERE student_id = ?
            """, (leaving_date, leaving_reason, student_id))
        else:
            cur.execute("""
                UPDATE students
                SET leaving_date = NULL, leaving_reason = NULL,
                    student_status = 'current', passout_year = NULL
                WHERE student_id = ?
            """, (student_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()


def get_students_by_status(academic_year=None, status='all'):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    if status == 'current':
        if academic_year:
            cur.execute(
                "SELECT * FROM students "
                "WHERE (student_status='current' OR student_status IS NULL) "
                "AND academic_year=? ORDER BY id DESC", (academic_year,)
            )
        else:
            cur.execute(
                "SELECT * FROM students "
                "WHERE student_status='current' OR student_status IS NULL "
                "ORDER BY id DESC"
            )
    elif status == 'passout':
        if academic_year:
            cur.execute(
                "SELECT * FROM students WHERE student_status='passout' "
                "AND academic_year=? ORDER BY id DESC", (academic_year,)
            )
        else:
            cur.execute(
                "SELECT * FROM students WHERE student_status='passout' ORDER BY id DESC"
            )
    else:
        if academic_year:
            cur.execute(
                "SELECT * FROM students WHERE academic_year=? ORDER BY id DESC",
                (academic_year,)
            )
        else:
            cur.execute("SELECT * FROM students ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_student_by_id(db_id: int) -> bool:
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM students WHERE id = ?", (db_id,))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            print(f"Error: {e}")
            return False



# ══════════════════════════════════════════════════════════════════
#  LC COUNT
# ══════════════════════════════════════════════════════════════════

def get_lc_count(student_db_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT lc_count FROM students WHERE id = ?", (student_db_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0


def get_lc_no(student_db_id: int) -> int | None:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT lc_no FROM students WHERE id = ?", (student_db_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else None


def get_next_lc_no() -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    # Get the maximum LC number from all students 
    cur.execute("SELECT COALESCE(MAX(lc_no), 0) FROM students")
    max_lc_no = cur.fetchone()[0]
    conn.close()
    # Return the next sequential number (max + 1)
    return max_lc_no + 1


def get_lc_number_for_print(student_db_id: int) -> int:
    return get_lc_no(student_db_id) or get_next_lc_no()


def increment_lc_count(student_db_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT lc_no FROM students WHERE id=?", (student_db_id,))
    row = cur.fetchone()
    lc_no = row[0] if row and row[0] else None
    if lc_no is None:
        # Assign the next sequential LC number for first-time LC students
        lc_no = get_next_lc_no()
    cur.execute(
        "UPDATE students SET lc_count = COALESCE(lc_count,0)+1, lc_no=? WHERE id=?",
        (lc_no, student_db_id)
    )
    conn.commit()
    cur.execute("SELECT lc_count FROM students WHERE id=?", (student_db_id,))
    new_count = cur.fetchone()[0]
    conn.close()
    return new_count


def mark_student_as_passout(student_db_id: int, passout_year: str | None = None) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    try:
        if passout_year:
            cur.execute(
                "UPDATE students SET student_status='passout', passout_year=? WHERE id=?",
                (passout_year, student_db_id)
            )
        else:
            cur.execute(
                "UPDATE students SET student_status='passout' WHERE id=?",
                (student_db_id,)
            )
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"[DB] Error marking student as passout: {e}")
        return False
    finally:
        conn.close()


def promote_student(
    student_db_id: int,
    new_class: str,
    new_academic_year: str | None = None,
    admission_date: str | None = None,
) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        parts = ["current_class = ?", "student_status = 'current'"]
        params: list = [new_class]
        if new_academic_year is not None:
            parts.append("academic_year = ?")
            params.append(new_academic_year)
        if admission_date is not None:
            parts.append("admission_date = ?")
            params.append(admission_date)
        params.append(student_db_id)
        cur.execute(
            f"UPDATE students SET {', '.join(parts)} WHERE id = ?",
            params,
        )
        updated = cur.rowcount
        if new_academic_year:
            cur.execute(
                "INSERT OR IGNORE INTO academic_years (academic_year) VALUES (?)",
                (new_academic_year,),
            )
        conn.commit()
        return updated > 0
    except Exception as e:
        print(f"[DB] Error promoting student: {e}")
        return False
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════
#  BONAFIDE COUNT
# ══════════════════════════════════════════════════════════════════

def get_bonafide_count(student_db_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT bonafide_count FROM students WHERE id=?", (student_db_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0


def increment_bonafide_count(student_db_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        "UPDATE students SET bonafide_count = COALESCE(bonafide_count,0)+1 WHERE id=?",
        (student_db_id,)
    )
    conn.commit()
    cur.execute("SELECT bonafide_count FROM students WHERE id=?", (student_db_id,))
    new_count = cur.fetchone()[0]
    conn.close()
    return new_count
