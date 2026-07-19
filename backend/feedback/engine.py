import json
from datetime import datetime
from typing import Dict, Any

from backend.vector_store.store import VectorStore
from backend.database.db import Database


class FeedbackEngine:
    def store_feedback(
        self,
        session_id: int,
        user_id: str,
        question: str,
        answer: str,
        evaluation: Dict[str, Any],
        vector_store: VectorStore,
        db: Database,
    ):
        score = evaluation.get("score", 5)
        topic = evaluation.get("topic", "general")
        star_score = evaluation.get("star_score", 0)
        coherence_score = evaluation.get("coherence_score", 0)
        keyword_score = evaluation.get("keyword_score", 0)
        matched_keywords = evaluation.get("matched_keywords", [])
        missing_keywords = evaluation.get("missing_keywords", [])

        feedback_text = (
            f"Strengths: {evaluation.get('strengths', '')}\n"
            f"Improvements: {evaluation.get('improvements', '')}\n"
            f"Better phrasing: {evaluation.get('better_phrasing', '')}"
        )

        db.save_answer(
            session_id=session_id,
            question=question,
            answer=answer,
            score=score,
            topic=topic,
            feedback_text=feedback_text,
            star_score=star_score,
            coherence_score=coherence_score,
            keyword_score=keyword_score,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
        )

        db.upsert_topic_progress(user_id, topic, score)

        qa_text = (
            f"Question: {question}\n"
            f"Answer: {answer}\n"
            f"Feedback: {feedback_text}\n"
            f"Score: {score}/10"
        )
        vector_store.add_documents(
            texts=[qa_text],
            metadatas=[
                {
                    "source": "past_answer",
                    "user_id": user_id,
                    "topic": topic,
                    "score": score,
                    "date": datetime.now().isoformat(),
                }
            ],
        )
