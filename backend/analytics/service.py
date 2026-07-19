from typing import List, Dict, Any

import pandas as pd

from backend.database.db import Database
from backend.vector_store.store import VectorStore


class AnalyticsService:
    def __init__(self, db: Database, vector_store: VectorStore):
        self.db = db
        self.vector_store = vector_store

    def get_topic_summary(self, user_id: str) -> List[Dict[str, Any]]:
        return self.db.get_user_topic_progress(user_id)

    def get_session_trend(self, user_id: str) -> pd.DataFrame:
        sessions = self.db.get_user_sessions(user_id)
        rows = []
        for sess in sessions:
            answers = self.db.get_session_answers(sess["id"])
            for ans in answers:
                rows.append(
                    {
                        "session_id": sess["id"],
                        "date": ans["created_at"][:10],
                        "topic": ans["topic"],
                        "score": ans["score"],
                    }
                )
        return pd.DataFrame(rows)

    def get_weakest_topics(self, user_id: str, threshold: float = 6.0) -> List[Dict[str, Any]]:
        topics = self.db.get_user_topic_progress(user_id)
        return [t for t in topics if t["avg_score"] < threshold]

    def get_low_score_answers(
        self, user_id: str, max_score: int = 5, limit: int = 5
    ) -> List[Dict[str, Any]]:
        results = self.vector_store.similarity_search(
            query="low score poor answer improvement needed",
            n_results=limit,
            filter_metadata={"user_id": user_id, "source": "past_answer"},
        )
        return results

    def get_recommendations(self, user_id: str) -> List[str]:
        weak = self.get_weakest_topics(user_id)
        if not weak:
            return ["Great progress! Keep practicing to maintain your skills."]
        recs = []
        for w in weak:
            recs.append(
                f"Focus on '{w['topic']}' (current avg: {w['avg_score']:.1f}/10). "
                f"Practice with scenario-based questions in this area."
            )
        return recs
