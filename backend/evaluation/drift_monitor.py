import math
from typing import List, Dict, Any

from backend.database.db import Database
from backend import config


class DriftMonitor:
    def __init__(self, db: Database):
        self.db = db

    def get_recent_scores(self, user_id: str, window: int = None) -> List[int]:
        window = window or config.DRIFT_WINDOW_SIZE
        sessions = self.db.get_user_sessions(user_id)
        scores = []
        for session in sessions:
            answers = self.db.get_session_answers(session["id"])
            for answer in answers:
                scores.append(answer["score"])
        return scores[-window:] if scores else []

    def compute_z_score(self, scores: List[int]) -> float:
        if len(scores) < 2:
            return 0.0
        latest = scores[-1]
        historical = scores[:-1]
        mean = sum(historical) / len(historical)
        variance = sum((s - mean) ** 2 for s in historical) / len(historical)
        std = math.sqrt(variance) if variance > 0 else 1e-10
        return (latest - mean) / std

    def check_drift(self, user_id: str) -> Dict[str, Any]:
        scores = self.get_recent_scores(user_id)
        if len(scores) < 3:
            return {
                "drifting": False,
                "z_score": 0.0,
                "recent_avg": sum(scores) / len(scores) if scores else 0.0,
                "overall_avg": sum(scores) / len(scores) if scores else 0.0,
                "message": "Not enough data to detect drift",
            }

        z = self.compute_z_score(scores)
        recent_avg = sum(scores) / len(scores)
        all_sessions = self.db.get_user_sessions(user_id)
        all_scores = []
        for s in all_sessions:
            for a in self.db.get_session_answers(s["id"]):
                all_scores.append(a["score"])
        overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0.0

        drifting = z < -config.DRIFT_Z_THRESHOLD

        if drifting:
            message = (
                f"Performance drift detected for user {user_id}. "
                f"Recent scores are significantly below average (z={z:.2f})."
            )
        else:
            message = f"No significant drift for user {user_id} (z={z:.2f})."

        return {
            "drifting": drifting,
            "z_score": round(z, 4),
            "recent_avg": round(recent_avg, 2),
            "overall_avg": round(overall_avg, 2),
            "message": message,
        }

    def get_all_users_drift(self) -> List[Dict[str, Any]]:
        user_ids = self.db.get_all_user_ids()
        results = []
        for uid in user_ids:
            result = self.check_drift(uid)
            result["user_id"] = uid
            results.append(result)
        return results
