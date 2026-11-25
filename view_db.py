"""
CaneCare AI - Database Viewer Script
Quickly inspect users, scans, predictions, and feedback stored in SQLite (canecare.db).
"""

import os
import sys
import sqlite3

current_dir = os.path.dirname(os.path.abspath(__file__))
# Check both root and canecare-backend directory
db_paths = [
    os.path.join(current_dir, "canecare-backend", "canecare.db"),
    os.path.join(current_dir, "canecare.db"),
]

db_path = None
for path in db_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("❌ No canecare.db found!")
    sys.exit(1)

print(f"\n📂 Database File: {db_path}\n" + "=" * 70)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def print_table(title, query):
    print(f"\n📌 {title}:")
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            print("   (No data / Empty table)")
            return
        
        cols = rows[0].keys()
        col_width = 24
        header = " | ".join(c.ljust(col_width)[:col_width] for c in cols)
        print("   " + header)
        print("   " + "-" * len(header))
        for r in rows:
            line = " | ".join(str(r[c] if r[c] is not None else "-").ljust(col_width)[:col_width] for c in cols)
            print("   " + line)
        print(f"   Total rows: {len(rows)}")
    except Exception as e:
        print(f"   Error reading table: {e}")

# 1. Users
print_table("USERS (नोंदणीकृत वापरकर्ते)", "SELECT id, full_name, email, phone, role, created_at FROM users")

# 2. Scans
print_table("SCANS (स्कॅन केलेल्या पानांचे रेकॉर्ड्स)", "SELECT id, user_id, image_path, created_at FROM scans")

# 3. Predictions
print_table("PREDICTIONS (AI रोगांचे निष्कर्ष)", "SELECT id, scan_id, class_label, confidence, severity, model_version FROM predictions")

# 4. Feedback
print_table("FEEDBACK (शेतकऱ्यांचा अभिप्राय)", "SELECT id, scan_id, is_correct, true_class, comment, created_at FROM feedback")

print("\n" + "=" * 70 + "\n")
conn.close()
