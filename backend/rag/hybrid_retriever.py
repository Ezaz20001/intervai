from typing import Dict, List, Any

from backend.vector_store.store import VectorStore
from backend.database.db import Database


class HybridRetriever:
    def __init__(self, vector_store: VectorStore, db: Database = None):
        self.vector_store = vector_store
        self.db = db or Database()

    def retrieve_skills_context(
        self, user_id: str, query: str, n: int = 5
    ) -> List[Dict[str, Any]]:
        return self.vector_store.similarity_search(
            query=query,
            n_results=n,
            filter_metadata={"user_id": user_id, "source": "cv"},
        )

    def retrieve_projects_context(
        self, user_id: str, query: str, n: int = 5
    ) -> List[Dict[str, Any]]:
        results = self.vector_store.similarity_search(
            query=query,
            n_results=n,
            filter_metadata={"user_id": user_id},
        )
        return [
            r for r in results
            if "project" in r.get("metadata", {}).get("topic", "").lower()
            or "project" in r.get("text", "").lower()
        ]

    def retrieve_all_context(
        self, user_id: str, query: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        skills = self.retrieve_skills_context(user_id, query)
        projects = self.retrieve_projects_context(user_id, query)
        return {"skills": skills, "projects": projects}

    def retrieve_for_question(
        self, user_id: str, question: str
    ) -> str:
        context_parts = []

        skills = self.retrieve_skills_context(user_id, question, n=3)
        if skills:
            skills_text = "\n".join(f"- {s['text']}" for s in skills)
            context_parts.append(f"Candidate Skills & Resume:\n{skills_text}")

        projects = self.retrieve_projects_context(user_id, question, n=3)
        if projects:
            projects_text = "\n".join(f"- {p['text']}" for p in projects)
            context_parts.append(f"Candidate Projects:\n{projects_text}")

        weak_areas = self.db.get_user_topic_progress(user_id)
        weak = [w for w in weak_areas if w["avg_score"] < 6.0]
        if weak:
            weak_text = "\n".join(
                f"- {w['topic']}: avg score {w['avg_score']:.1f}"
                for w in weak
            )
            context_parts.append(f"Weak Areas to Focus On:\n{weak_text}")

        return "\n\n".join(context_parts) if context_parts else "No context available."
