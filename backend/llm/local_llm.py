import json
import re
from typing import Dict, Any

from backend import config


class LocalLLMService:
    def __init__(
        self,
        model_name: str = None,
        bits: int = None,
        temperature: float = None,
        max_tokens: int = None,
    ):
        self.model_name = model_name or config.LOCAL_LLM_MODEL
        self.bits = bits or config.LOCAL_LLM_BITS
        self.temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
        self.max_tokens = max_tokens or config.LLM_MAX_TOKENS
        self._model = None
        self._tokenizer = None
        self._load_error = None

    def _ensure_loaded(self):
        if self._model is not None or self._load_error is not None:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

            if not torch.cuda.is_available():
                self._load_error = (
                    "No CUDA GPU available. Local LLM requires a GPU. "
                    "Install bitsandbytes and ensure a compatible GPU is present."
                )
                return

            quantization_config = BitsAndBytesConfig(
                load_in_4bit=(self.bits == 4),
                load_in_8bit=(self.bits == 8),
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map="auto",
                torch_dtype=torch.float16,
            )
        except ImportError as e:
            self._load_error = (
                f"Missing dependency: {e}. "
                "Install with: pip install transformers bitsandbytes accelerate"
            )
        except Exception as e:
            self._load_error = f"Failed to load local LLM: {e}"

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        self._ensure_loaded()
        if self._load_error:
            raise RuntimeError(self._load_error)

        import torch

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        input_text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(input_text, return_tensors="pt").to(self._model.device)

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                do_sample=True,
                top_p=0.9,
            )

        generated = outputs[0][inputs["input_ids"].shape[-1]:]
        return self._tokenizer.decode(generated, skip_special_tokens=True).strip()

    def generate_question(
        self, system_prompt: str, history: str, context: str
    ) -> str:
        user_prompt = (
            f"Interview context:\n{context}\n\n"
            f"Conversation so far:\n{history}\n\n"
            "Ask the next interview question. Return only the question text."
        )
        return self._call(system_prompt, user_prompt)

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
