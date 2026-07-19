import sqlite3
import json
import threading
from datetime import datetime
from typing import List, Optional, Dict, Any

from backend import config
from backend.database.models import ALL_TABLES


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._create_tables()

    def _create_tables(self):
        with self._lock:
            cursor = self.conn.cursor()
            for table_sql in ALL_TABLES:
                cursor.execute(table_sql)
            self.conn.commit()
            self._migrate(cursor)

    def _migrate(self, cursor):
        try:
            cursor.execute("PRAGMA table_info(answers)")
            cols = {row[1] for row in cursor.fetchall()}
            # Whitelist pattern: column names and types are hardcoded dicts, not user input
            _VALID_COLUMNS = {
                "star_score": "INTEGER DEFAULT 0",
                "coherence_score": "INTEGER DEFAULT 0",
                "keyword_score": "INTEGER DEFAULT 0",
                "matched_keywords": "TEXT DEFAULT '[]'",
                "missing_keywords": "TEXT DEFAULT '[]'",
            }
            for col, typedef in _VALID_COLUMNS.items():
                assert col.isidentifier(), f"Column name {col!r} is not a valid SQL identifier"
                if col not in cols:
                    cursor.execute(f"ALTER TABLE answers ADD COLUMN {col} {typedef}")
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS score_history ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "user_id TEXT NOT NULL, score INTEGER NOT NULL, "
                "session_id INTEGER, created_at TEXT NOT NULL)"
            )
            self.conn.commit()
        except Exception:
            pass

    # --- Sessions ---

    def create_session(self, user_id: str, job_role: str = "") -> int:
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (user_id, job_role, started_at) VALUES (?, ?, ?)",
                (user_id, job_role, now),
            )
            self.conn.commit()
            return cursor.lastrowid

    def end_session(self, session_id: int):
        now = datetime.now().isoformat()
        with self._lock:
            self.conn.execute(
                "UPDATE sessions SET ended_at = ? WHERE id = ?", (now, session_id)
            )
            self.conn.commit()

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM sessions WHERE user_id = ? ORDER BY started_at DESC", (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Answers ---

    def save_answer(
        self,
        session_id: int,
        question: str,
        answer: str,
        score: int,
        topic: str,
        feedback_text: str,
        star_score: int = 0,
        coherence_score: int = 0,
        keyword_score: int = 0,
        matched_keywords: Optional[List[str]] = None,
        missing_keywords: Optional[List[str]] = None,
    ) -> int:
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO answers (session_id, question, answer, score, topic, feedback_text, "
                "star_score, coherence_score, keyword_score, matched_keywords, missing_keywords, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id, question, answer, score, topic, feedback_text,
                    star_score, coherence_score, keyword_score,
                    json.dumps(matched_keywords or []),
                    json.dumps(missing_keywords or []),
                    now,
                ),
            )
            self.conn.commit()
            return cursor.lastrowid

    def get_session_answers(self, session_id: int) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM answers WHERE session_id = ? ORDER BY created_at", (session_id,)
            )
            rows = []
            for row in cursor.fetchall():
                d = dict(row)
                try:
                    d["matched_keywords"] = json.loads(d.get("matched_keywords", "[]"))
                except (json.JSONDecodeError, TypeError):
                    d["matched_keywords"] = []
                try:
                    d["missing_keywords"] = json.loads(d.get("missing_keywords", "[]"))
                except (json.JSONDecodeError, TypeError):
                    d["missing_keywords"] = []
                rows.append(d)
            return rows

    def get_all_answers(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.execute(
                "SELECT a.* FROM answers a "
                "JOIN sessions s ON a.session_id = s.id "
                "WHERE s.user_id = ? ORDER BY a.created_at DESC LIMIT ?",
                (user_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    # --- Topic Progress ---

    def upsert_topic_progress(self, user_id: str, topic: str, score: int):
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM topic_progress WHERE user_id = ? AND topic = ?",
                (user_id, topic),
            )
            row = cursor.fetchone()
            if row:
                new_total = row["total_answers"] + 1
                new_avg = ((row["avg_score"] * row["total_answers"]) + score) / new_total
                cursor.execute(
                    "UPDATE topic_progress SET avg_score = ?, total_answers = ?, last_practiced = ? "
                    "WHERE user_id = ? AND topic = ?",
                    (new_avg, new_total, now, user_id, topic),
                )
            else:
                cursor.execute(
                    "INSERT INTO topic_progress (user_id, topic, avg_score, total_answers, last_practiced) "
                    "VALUES (?, ?, ?, 1, ?)",
                    (user_id, topic, float(score), now),
                )
            self.conn.commit()

    def get_user_topic_progress(self, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM topic_progress WHERE user_id = ? ORDER BY avg_score ASC",
                (user_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all_user_ids(self) -> List[str]:
        with self._lock:
            cursor = self.conn.execute("SELECT DISTINCT user_id FROM sessions")
            return [row["user_id"] for row in cursor.fetchall()]

    # --- Score History for Drift Monitoring ---

    def log_score(self, user_id: str, score: int, session_id: int = None):
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO score_history (user_id, score, session_id, created_at) VALUES (?, ?, ?, ?)",
                (user_id, score, session_id, now),
            )
            self.conn.commit()

    def get_score_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.execute(
                "SELECT * FROM score_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all_sessions_with_answers(self) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.execute(
                "SELECT s.*, COUNT(a.id) as answer_count, AVG(a.score) as avg_score "
                "FROM sessions s LEFT JOIN answers a ON s.id = a.session_id "
                "GROUP BY s.id ORDER BY s.started_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def close(self):
        with self._lock:
            self.conn.close()
