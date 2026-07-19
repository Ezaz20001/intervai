import sqlite3

conn = sqlite3.connect("data/progress.db")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(answers)")
cols = [row[1] for row in cursor.fetchall()]
print("Current columns:", cols)

needed = ["star_score", "coherence_score", "keyword_score", "matched_keywords", "missing_keywords"]
for c in needed:
    if c not in cols:
        if c in ("matched_keywords", "missing_keywords"):
            cursor.execute(f"ALTER TABLE answers ADD COLUMN {c} TEXT DEFAULT '[]'")
        else:
            cursor.execute(f"ALTER TABLE answers ADD COLUMN {c} INTEGER DEFAULT 0")
        print(f"Added: {c}")
    else:
        print(f"Exists: {c}")

cursor.execute("CREATE TABLE IF NOT EXISTS score_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, score INTEGER NOT NULL, session_id INTEGER, created_at TEXT NOT NULL)")
print("score_history table ensured")

conn.commit()
conn.close()
print("Migration done")
