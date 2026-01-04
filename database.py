import sqlite3
from datetime import date

conn = sqlite3.connect("salary.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    amount INTEGER,
    note TEXT,
    date TEXT
)
""")
conn.commit()

def add_txn(txn_type, amount, note=""):
    cur.execute(
        "INSERT INTO transactions (type, amount, note, date) VALUES (?, ?, ?, ?)",
        (txn_type, amount, note, str(date.today()))
    )
    conn.commit()

def get_today():
    cur.execute("SELECT type, amount FROM transactions WHERE date=?", (str(date.today()),))
    return cur.fetchall()

def get_all():
    cur.execute("SELECT type, amount FROM transactions")
    return cur.fetchall()
