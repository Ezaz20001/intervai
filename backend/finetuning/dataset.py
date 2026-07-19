import json
from typing import Dict, List, Optional
from collections import Counter

from backend.database.db import Database


class DatasetCurator:
    def curate_from_db(self, db: Database, user_id: Optional[str] = None) -> List[Dict]:
        if user_id:
            answers = db.get_all_answers(user_id, limit=1000)
        else:
            all_sessions = db.get_all_sessions_with_answers()
            answers = []
            for session in all_sessions:
                session_answers = db.get_session_answers(session["id"])
                answers.extend(session_answers)

        curated = []
        for answer in answers:
            score = answer.get("score", 0)
            if score >= 7:
                label = "good"
            elif score <= 4:
                label = "bad"
            else:
                continue
            curated.append({
                "question": answer["question"],
                "answer": answer["answer"],
                "label": label,
                "score": score,
                "topic": answer.get("topic", "general"),
            })
        return curated

    def export_to_jsonl(self, data: List[Dict], output_path: str):
        with open(output_path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def get_training_stats(self, data: List[Dict]) -> Dict:
        if not data:
            return {
                "total": 0,
                "good_count": 0,
                "bad_count": 0,
                "avg_score": 0.0,
                "topic_distribution": {},
            }

        good_count = sum(1 for d in data if d["label"] == "good")
        bad_count = sum(1 for d in data if d["label"] == "bad")
        scores = [d["score"] for d in data]
        avg_score = sum(scores) / len(scores)

        topic_counts = Counter(d.get("topic", "general") for d in data)

        return {
            "total": len(data),
            "good_count": good_count,
            "bad_count": bad_count,
            "avg_score": round(avg_score, 2),
            "topic_distribution": dict(topic_counts),
        }
