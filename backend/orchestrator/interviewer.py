from typing import List, Dict, Any, Optional

from backend.llm.service import LLMService
from backend.vector_store.store import VectorStore
from backend.database.db import Database
from backend.feedback.engine import FeedbackEngine
from backend.rag.hybrid_retriever import HybridRetriever
from backend.rag.reranker import CrossEncoderReranker
from backend.grader.star_grader import STARGrader
from backend.guardrails.input_guardrail import InputGuardrail
from backend import config


class InterviewOrchestrator:
    def __init__(
        self,
        llm: LLMService,
        vector_store: VectorStore,
        db: Database,
        feedback_engine: FeedbackEngine,
    ):
        self.llm = llm
        self.vector_store = vector_store
        self.db = db
        self.feedback_engine = feedback_engine
        self._session_id: Optional[int] = None
        self._user_id: Optional[str] = None
        self._question_count = 0
        self._history: List[Dict[str, str]] = []
        self._cited_entries: List[Dict[str, str]] = []

        self.hybrid_retriever = HybridRetriever(vector_store, db)
        self.reranker = CrossEncoderReranker()
        self.star_grader = STARGrader()
        self.guardrail = InputGuardrail()

    @property
    def session_id(self) -> Optional[int]:
        return self._session_id

    @property
    def is_active(self) -> bool:
        return self._session_id is not None and self._question_count < config.SESSION_QUESTION_LIMIT

    @property
    def cited_entries(self) -> List[Dict[str, str]]:
        return self._cited_entries

    def start_session(self, user_id: str, job_role: str = ""):
        self._session_id = self.db.create_session(user_id, job_role)
        self._user_id = user_id
        self._question_count = 0
        self._history = []
        self._cited_entries = []

    def _build_system_prompt(self) -> str:
        context = self.hybrid_retriever.retrieve_all_context(
            self._user_id, ""
        )
        weak_areas = self.db.get_user_topic_progress(self._user_id)
        weak_topics = [w for w in weak_areas if w["avg_score"] < 6.0]

        cv_text = "\n".join(c["text"] for c in context.get("skills", []))
        cv_text += "\n" + "\n".join(c["text"] for c in context.get("projects", []))

        jd_chunks = self.vector_store.similarity_search(
            "job responsibilities, requirements",
            n_results=5,
            filter_metadata={"user_id": self._user_id, "source": "jd"},
        )
        jd_text = "\n".join(c["text"] for c in jd_chunks)

        weak_text = ""
        if weak_topics:
            weak_text = "Focus on weak areas: " + ", ".join(
                f"{w['topic']} (avg {w['avg_score']:.1f}/10)" for w in weak_topics
            )

        prompt = (
            f"You are a personalized interview coach. The candidate's CV:\n{cv_text}\n\n"
            f"Job Description:\n{jd_text}\n\n"
            f"{weak_text}\n\n"
            "Ask realistic, challenging interview questions. Evaluate answers fairly. "
            "Adapt question difficulty based on prior answers. "
            f"Limit to {config.SESSION_QUESTION_LIMIT} questions total."
        )
        return prompt

    def next_question(self) -> str:
        context = self._build_system_prompt()
        history_str = "\n".join(
            f"Q: {h['q']}\nA: {h['a']}" for h in self._history
        ) or "No questions yet."
        question = self.llm.generate_question(context, history_str, context)
        self._question_count += 1
        self._history.append({"q": question, "a": ""})

        skills_ctx = self.hybrid_retriever.retrieve_skills_context(
            self._user_id, question, n=2
        )
        projects_ctx = self.hybrid_retriever.retrieve_projects_context(
            self._user_id, question, n=2
        )
        all_entries = skills_ctx + projects_ctx
        if all_entries:
            reranked = self.reranker.rerank(question, all_entries, top_k=3)
            self._cited_entries = [
                {"text": r["text"][:200], "source": r["metadata"].get("source", "cv")}
                for r in reranked
            ]
        else:
            self._cited_entries = []

        return question

    def submit_answer(self, answer: str) -> Dict[str, Any]:
        if not self._history or self._history[-1]["a"]:
            return {"error": "No active question to answer."}

        guardrail_result = self.guardrail.validate(answer, self._history[-1]["q"])
        if not guardrail_result.get("safe", True):
            return {
                "question": self._history[-1]["q"],
                "answer": answer,
                "score": 0,
                "topic": "guardrail",
                "strengths": "",
                "improvements": f"Response blocked: {guardrail_result.get('reason', 'unsafe content')}",
                "better_phrasing": "",
                "finished": False,
                "blocked": True,
                "guardrail_reason": guardrail_result.get("reason", ""),
            }

        self._history[-1]["a"] = answer
        question = self._history[-1]["q"]

        jd_chunks = self.vector_store.similarity_search(
            "job responsibilities, requirements",
            n_results=3,
            filter_metadata={"user_id": self._user_id, "source": "jd"},
        )
        job_context = "\n".join(c["text"] for c in jd_chunks)

        evaluation = self.star_grader.grade_answer(
            question, answer, job_context, self.llm
        )

        self.feedback_engine.store_feedback(
            session_id=self._session_id,
            user_id=self._user_id,
            question=question,
            answer=answer,
            evaluation=evaluation,
            vector_store=self.vector_store,
            db=self.db,
        )

        if hasattr(self.db, 'log_score'):
            self.db.log_score(self._user_id, evaluation.get("score", 5), self._session_id)

        finished = not self.is_active
        response = {
            "question": question,
            "answer": answer,
            "score": evaluation.get("score", 5),
            "topic": evaluation.get("topic", "general"),
            "strengths": evaluation.get("strengths", ""),
            "improvements": evaluation.get("improvements", ""),
            "better_phrasing": evaluation.get("better_phrasing", ""),
            "star_score": evaluation.get("star_score", 5),
            "coherence_score": evaluation.get("coherence_score", 5),
            "keyword_score": evaluation.get("keyword_score", 5),
            "matched_keywords": evaluation.get("matched_keywords", []),
            "missing_keywords": evaluation.get("missing_keywords", []),
            "cited_entries": self._cited_entries,
            "finished": finished,
        }
        return response

    def end_session(self):
        if self._session_id:
            self.db.end_session(self._session_id)
            self._session_id = None
            self._user_id = None
            self._question_count = 0
            self._history = []
            self._cited_entries = []
