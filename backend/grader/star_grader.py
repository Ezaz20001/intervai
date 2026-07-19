import json
import re
from typing import Any, Dict

from backend import config


class STARGrader:

    def _build_grading_prompt(self) -> str:
        return (
            "You are an expert interview answer grader. Evaluate the candidate's "
            "answer on three dimensions and return a JSON object.\n\n"
            "SCORING DIMENSIONS:\n\n"
            "1. STAR format (score 1-10): Evaluate whether the answer follows the "
            "STAR framework:\n"
            "   - Situation: Did the candidate describe the context?\n"
            "   - Task: Did they explain their specific responsibility?\n"
            "   - Action: Did they detail the concrete steps they took?\n"
            "   - Result: Did they share measurable outcomes or impact?\n"
            "   Score 10 = all four components present with rich detail.\n"
            "   Score 1 = none of the components are identifiable.\n\n"
            "2. Coherence (score 1-10): Evaluate the logical flow and clarity:\n"
            "   - Are ideas connected logically?\n"
            "   - Is the answer easy to follow?\n"
            "   - Is it concise without unnecessary rambling?\n"
            "   - Does it directly address the question asked?\n\n"
            "3. Keyword coverage (score 1-10): Evaluate how many job-relevant "
            "keywords from the job context appear naturally in the answer:\n"
            "   - Technical skills mentioned in the job posting\n"
            "   - Domain-specific terminology\n"
            "   - Role-relevant concepts\n"
            "   Score 10 = answer naturally incorporates most job-relevant keywords.\n"
            "   Score 1 = answer contains zero job-relevant keywords.\n\n"
            "4. Overall score: Weighted average = STAR * 0.40 + Coherence * 0.30 + "
            "Keywords * 0.30. Round to nearest integer, clamp to 1-10.\n\n"
            "REQUIRED JSON OUTPUT FORMAT:\n"
            "{\n"
            '  "star_score": <int 1-10>,\n'
            '  "coherence_score": <int 1-10>,\n'
            '  "keyword_score": <int 1-10>,\n'
            '  "overall_score": <int 1-10>,\n'
            '  "matched_keywords": ["keyword1", "keyword2", ...],\n'
            '  "missing_keywords": ["keyword3", "keyword4", ...],\n'
            '  "star_components": {\n'
            '    "situation": <true|false>,\n'
            '    "task": <true|false>,\n'
            '    "action": <true|false>,\n'
            '    "result": <true|false>\n'
            "  },\n"
            '  "reasoning": "<brief explanation of the scores>"\n'
            "}\n\n"
            "Return ONLY valid JSON. No markdown fences, no extra text."
        )

    def grade_answer(
        self, question: str, answer: str, job_context: str, llm_service
    ) -> Dict[str, Any]:
        system_prompt = self._build_grading_prompt()
        user_prompt = (
            f"Job requirements context:\n{job_context}\n\n"
            f"Interview question: {question}\n"
            f"Candidate answer: {answer}\n\n"
            "Evaluate the answer across all three dimensions and return JSON."
        )
        raw = llm_service._call(system_prompt, user_prompt)
        return self._parse_grading_response(raw)

    def _parse_grading_response(self, raw: str) -> Dict[str, Any]:
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            data = json.loads(cleaned)
            star = data.get("star_components", {})
            return {
                "star_score": int(data.get("star_score", 5)),
                "coherence_score": int(data.get("coherence_score", 5)),
                "keyword_score": int(data.get("keyword_score", 5)),
                "overall_score": int(data.get("overall_score", 5)),
                "matched_keywords": data.get("matched_keywords", []),
                "missing_keywords": data.get("missing_keywords", []),
                "star_components": {
                    "situation": bool(star.get("situation", False)),
                    "task": bool(star.get("task", False)),
                    "action": bool(star.get("action", False)),
                    "result": bool(star.get("result", False)),
                },
                "reasoning": data.get("reasoning", ""),
            }
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

        star_match = re.search(r'"star_score":\s*(\d+)', raw)
        coherence_match = re.search(r'"coherence_score":\s*(\d+)', raw)
        keyword_match = re.search(r'"keyword_score":\s*(\d+)', raw)
        overall_match = re.search(r'"overall_score":\s*(\d+)', raw)

        star_score = int(star_match.group(1)) if star_match else 5
        coherence_score = int(coherence_match.group(1)) if coherence_match else 5
        keyword_score = int(keyword_match.group(1)) if keyword_match else 5
        overall_score = int(overall_match.group(1)) if overall_match else 5

        matched = re.findall(r'"matched_keywords":\s*\[([^\]]*)\]', raw)
        matched_kw = re.findall(r'"([^"]+)"', matched[0]) if matched else []

        missing = re.findall(r'"missing_keywords":\s*\[([^\]]*)\]', raw)
        missing_kw = re.findall(r'"([^"]+)"', missing[0]) if missing else []

        return {
            "star_score": max(1, min(10, star_score)),
            "coherence_score": max(1, min(10, coherence_score)),
            "keyword_score": max(1, min(10, keyword_score)),
            "overall_score": max(1, min(10, overall_score)),
            "matched_keywords": matched_kw,
            "missing_keywords": missing_kw,
            "star_components": {
                "situation": "situation" in raw.lower(),
                "task": "task" in raw.lower(),
                "action": "action" in raw.lower(),
                "result": "result" in raw.lower(),
            },
            "reasoning": "Parsed from unstructured LLM output.",
        }
