SESSION_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    job_role TEXT DEFAULT '',
    started_at TEXT NOT NULL,
    ended_at TEXT
)
"""

ANSWERS_TABLE = """
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    topic TEXT DEFAULT '',
    feedback_text TEXT DEFAULT '',
    star_score INTEGER DEFAULT 0,
    coherence_score INTEGER DEFAULT 0,
    keyword_score INTEGER DEFAULT 0,
    matched_keywords TEXT DEFAULT '[]',
    missing_keywords TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
)
"""

TOPIC_PROGRESS_TABLE = """
CREATE TABLE IF NOT EXISTS topic_progress (
    user_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    avg_score REAL DEFAULT 0.0,
    total_answers INTEGER DEFAULT 0,
    last_practiced TEXT DEFAULT '',
    PRIMARY KEY (user_id, topic)
)
"""

SCORE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS score_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    session_id INTEGER,
    created_at TEXT NOT NULL
)
"""

DRIFT_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS drift_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    z_score REAL NOT NULL,
    recent_avg REAL NOT NULL,
    overall_avg REAL NOT NULL,
    message TEXT DEFAULT '',
    created_at TEXT NOT NULL
)
"""

ALL_TABLES = [SESSION_TABLE, ANSWERS_TABLE, TOPIC_PROGRESS_TABLE, SCORE_HISTORY_TABLE, DRIFT_ALERTS_TABLE]
