import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras

from backend import config

_SESSION_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    job_role VARCHAR(255) DEFAULT '',
    started_at VARCHAR(30) NOT NULL,
    ended_at VARCHAR(30)
)
"""

_ANSWERS_TABLE = """
CREATE TABLE IF NOT EXISTS answers (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    topic VARCHAR(255) DEFAULT '',
    feedback_text TEXT DEFAULT '',
    created_at VARCHAR(30) NOT NULL
)
"""

_TOPIC_PROGRESS_TABLE = """
CREATE TABLE IF NOT EXISTS topic_progress (
    user_id VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    avg_score DOUBLE PRECISION DEFAULT 0.0,
    total_answers INTEGER DEFAULT 0,
    last_practiced VARCHAR(30) DEFAULT '',
    PRIMARY KEY (user_id, topic)
)
"""

_SCORE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS score_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    score INTEGER NOT NULL,
    session_id INTEGER REFERENCES sessions(id),
    created_at VARCHAR(30) NOT NULL
)
"""

_ALL_TABLES = [_SESSION_TABLE, _ANSWERS_TABLE, _TOPIC_PROGRESS_TABLE, _SCORE_HISTORY_TABLE]


class PostgresDatabase:
    def __init__(self):
        self._lock = threading.Lock()
        self.conn = psycopg2.connect(config.POSTGRES_URL)
        self.conn.autocommit = False

    def initialize(self):
        with self._lock:
            cursor = self.conn.cursor()
            for table_sql in _ALL_TABLES:
                cursor.execute(table_sql)
            self.conn.commit()

    def create_session(self, user_id: str, job_role: str = "") -> int:
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (user_id, job_role, started_at) VALUES (%s, %s, %s) RETURNING id",
                (user_id, job_role, now),
            )
            session_id = cursor.fetchone()[0]
            self.conn.commit()
            return session_id

    def end_session(self, session_id: int):
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE sessions SET ended_at = %s WHERE id = %s",
                (now, session_id),
            )
            self.conn.commit()

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT * FROM sessions WHERE id = %s", (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                "SELECT * FROM sessions WHERE user_id = %s ORDER BY started_at DESC",
                (user_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def save_answer(
        self,
        session_id: int,
        question: str,
        answer: str,
        score: int,
        topic: str,
        feedback_text: str,
    ) -> int:
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO answers (session_id, question, answer, score, topic, feedback_text, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (session_id, question, answer, score, topic, feedback_text, now),
            )
            answer_id = cursor.fetchone()[0]
            self.conn.commit()
            return answer_id

    def get_session_answers(self, session_id: int) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                "SELECT * FROM answers WHERE session_id = %s ORDER BY created_at",
                (session_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def upsert_topic_progress(self, user_id: str, topic: str, score: int):
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM topic_progress WHERE user_id = %s AND topic = %s",
                (user_id, topic),
            )
            row = cursor.fetchone()
            if row:
                existing_total = row[3]
                existing_avg = row[2]
                new_total = existing_total + 1
                new_avg = ((existing_avg * existing_total) + score) / new_total
                cursor.execute(
                    "UPDATE topic_progress SET avg_score = %s, total_answers = %s, last_practiced = %s "
                    "WHERE user_id = %s AND topic = %s",
                    (new_avg, new_total, now, user_id, topic),
                )
            else:
                cursor.execute(
                    "INSERT INTO topic_progress (user_id, topic, avg_score, total_answers, last_practiced) "
                    "VALUES (%s, %s, %s, 1, %s)",
                    (user_id, topic, float(score), now),
                )
            self.conn.commit()

    def get_user_topic_progress(self, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                "SELECT * FROM topic_progress WHERE user_id = %s ORDER BY avg_score ASC",
                (user_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all_user_ids(self) -> List[str]:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT user_id FROM sessions")
            return [row[0] for row in cursor.fetchall()]

    def log_score(self, user_id: str, score: int, session_id: int):
        now = datetime.now().isoformat()
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO score_history (user_id, score, session_id, created_at) "
                "VALUES (%s, %s, %s, %s)",
                (user_id, score, session_id, now),
            )
            self.conn.commit()

    def get_score_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(
                "SELECT * FROM score_history WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                (user_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def close(self):
        with self._lock:
            self.conn.close()
