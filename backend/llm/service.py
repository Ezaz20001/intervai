import json
import re
from typing import Dict, Any, Optional

from groq import Groq

from backend import config


class LLMService:
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.LLM_MODEL
        self._local_service = None

    @property
    def _backend(self):
        if config.USE_LOCAL_LLM and self._local_service is None:
            try:
                from backend.llm.local_llm import LocalLLMService
                self._local_service = LocalLLMService()
            except Exception:
                self._local_service = False
        if self._local_service and self._local_service is not False:
            return self._local_service
        return self

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        if not config.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Create a .env file in the project root "
                "with: GROQ_API_KEY=gsk_your_key_here"
            )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            raise RuntimeError(
                "Groq API call failed. Check your internet connection and API key."
            ) from e
        return response.choices[0].message.content.strip()

    def _call_plain(self, system_prompt: str, user_prompt: str) -> str:
        if not config.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set.")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
            )
        except Exception as e:
            raise RuntimeError("Groq API call failed.") from e
        return response.choices[0].message.content.strip()

    def generate_question(
        self, system_prompt: str, history: str, context: str
    ) -> str:
        user_prompt = (
            f"Interview context:\n{context}\n\n"
            f"Conversation so far:\n{history}\n\n"
            "Ask the next interview question. Return only the question text."
        )
        return self._call_plain(system_prompt, user_prompt)

    def dual_persona_call(
        self, system_prompt: str, user_prompt: str
    ) -> Dict[str, Any]:
        dual_system = (
            f"{system_prompt}\n\n"
            "You must respond with a JSON object containing exactly two keys:\n"
            '1. "interviewer": the next question to ask the candidate\n'
            '2. "grader": a JSON object with grading criteria for the previous answer (if any), '
            "containing: score (1-10), star_score (1-10), coherence_score (1-10), "
            "keyword_score (1-10), strengths (string), improvements (string), "
            "better_phrasing (string), matched_keywords (list), missing_keywords (list)\n\n"
            'If there is no previous answer to grade, set "grader" to null.\n'
            "Return ONLY valid JSON."
        )
        raw = self._call(dual_system, user_prompt)
        return self._parse_dual_response(raw)

    def _parse_dual_response(self, raw: str) -> Dict[str, Any]:
        raw = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            data = json.loads(raw)
            if "interviewer" in data and "grader" in data:
                return data
        except json.JSONDecodeError:
            pass
        q_match = re.search(r'"interviewer":\s*"([^"]+)"', raw)
        return {
            "interviewer": q_match.group(1) if q_match else raw,
            "grader": None,
        }

    def evaluate_answer(
        self, question: str, answer: str, job_context: str
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are an expert interview evaluator. Evaluate the candidate's answer "
            "and return a JSON object with these fields:\n"
            "- score: integer 1-10\n"
            "- topic: one word category (e.g., leadership, teamwork, technical, "
            "communication, problem_solving, experience, motivation, cultural_fit)\n"
            "- strengths: string (2-3 bullet points)\n"
            "- improvements: string (1-2 areas to improve)\n"
            "- better_phrasing: string (a rewritten better version of the answer)\n\n"
            "Return ONLY valid JSON. No markdown fences."
        )
        user_prompt = (
            f"Job requirements context:\n{job_context}\n\n"
            f"Question: {question}\n"
            f"Candidate's answer: {answer}\n\n"
            "Evaluate the answer and return JSON."
        )
        raw = self._call(system_prompt, user_prompt)
        return self._parse_feedback(raw)

    def _parse_feedback(self, raw: str) -> Dict[str, Any]:
        raw = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            score_match = re.search(r'"score":\s*(\d+)', raw)
            topic_match = re.search(r'"topic":\s*"([^"]+)"', raw)
            return {
                "score": int(score_match.group(1)) if score_match else 5,
                "topic": topic_match.group(1) if topic_match else "general",
                "strengths": "Evaluation parsed from raw output.",
                "improvements": "Consider providing more specific examples.",
                "better_phrasing": raw,
            }
