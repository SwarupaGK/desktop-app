import sqlite3

from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Total count
cur.execute("SELECT COUNT(*) FROM students")
print(f"Total Students: {cur.fetchone()[0]}")

# Show all records
cur.execute("SELECT id, student_id, name_mr, current_class FROM students")
rows = cur.fetchall()

if rows:
    for row in rows:
        print(f"ID: {row['id']} | Student ID: {row['student_id']} | Name: {row['name_mr']} | Class: {row['current_class']}")
else:
    print("No records found in database!")

conn.close()
