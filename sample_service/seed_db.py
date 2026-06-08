# sample_service/seed_db.py
import sqlite3
import os

def seed_db():
    os.makedirs("sample_service", exist_ok=True)
    conn = sqlite3.connect("sample_service/transactions.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            tx_id TEXT PRIMARY KEY,
            user_id TEXT,
            amount REAL,
            status TEXT,
            created_at TEXT
        )
    ''')

    cursor.executemany(
        "INSERT OR IGNORE INTO transactions VALUES (?,?,?,?,?)",
        [
            ("TX-1234", "USR-99",  250.00, "FAILED",  "2024-01-15 14:23:09"),
            ("TX-1235", "USR-12",  100.00, "SUCCESS", "2024-01-15 14:20:00"),
            ("TX-1236", None,      500.00, "FAILED",  "2024-01-15 14:22:00"),
        ]
    )

    conn.commit()
    conn.close()
    print("[Setup] Database seeded.")

if __name__ == "__main__":
    seed_db()