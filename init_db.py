"""
Creates database.db with exactly two tables, as required:

  users(id, username, password)
  reviews(id, movie, review_text, sentiment)

No foreign key between them on purpose -- reviews are anonymous/global.
"""
import sqlite3

DB_PATH = "database.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie TEXT NOT NULL,
    review_text TEXT NOT NULL,
    sentiment TEXT NOT NULL
)
""")

conn.commit()
conn.close()
print(f"Initialized {DB_PATH} with 'users' and 'reviews' tables.")
