import re
from typing import Dict, Any

from backend import config


class InputGuardrail:
    INJECTION_PATTERNS = [
        r"ignore\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions?|prompts?|rules?|guidelines?)",
        r"you\s+are\s+now\s+(?:a|an|the)",
        r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?|context)",
        r"(?:system|assistant|human)\s*:",
        r"<\s*(?:system|assistant|human)\s*>",
        r"(?:pretend|act\s+as\s+if|imagine)\s+(?:you\s+are|I\s+am)",
        r"(?:new|override|override)\s+(?:instructions?|system\s*prompt|rules?)",
        r"(?:forget|unlearn|reset)\s+(?:everything|all|your)\s+(?:instructions?|training|rules?)",
        r"(?:do\s+not|don'?t)\s+(?:follow|obey|listen\s+to)\s+(?:your|the)\s+(?:instructions?|rules?|guidelines?)",
        r"(?:jailbreak|DAN|do\s+anything\s+now)",
        r"(?:reveal|show|print|output)\s+(?:your|the)\s+(?:system\s*prompt|instructions?|rules?)",
        r"(?:what|tell\s+me)\s+(?:are|is)\s+your\s+(?:system\s*prompt|instructions?|initial\s*prompt)",
    ]

    OFFTOPIC_SHORT_THRESHOLD = 3

    def check_injection(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower().strip()

        for pattern in self.INJECTION_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                return {
                    "safe": False,
                    "reason": f"Potential prompt injection detected: matched pattern '{match.group()}'",
                    "confidence": config.GUARDRAIL_INJECTION_THRESHOLD,
                }

        role_playing = re.findall(
            r"\b(?:you\s+are|I\s+am|act\s+as|roleplay|role\s*play)\b", text_lower
        )
        if len(role_playing) >= 2:
            return {
                "safe": False,
                "reason": "Possible role-playing injection attempt detected",
                "confidence": 0.7,
            }

        return {
            "safe": True,
            "reason": "No injection patterns detected",
            "confidence": 1.0 - config.GUARDRAIL_INJECTION_THRESHOLD,
        }

    def check_offtopic(
        self, text: str, context: str = ""
    ) -> Dict[str, Any]:
        text_stripped = text.strip()
        word_count = len(text_stripped.split())

        if word_count < self.OFFTOPIC_SHORT_THRESHOLD:
            return {
                "on_topic": False,
                "reason": f"Response too short ({word_count} words), expected substantive answer",
                "confidence": 0.8,
            }

        if text_stripped.endswith("?"):
            return {
                "on_topic": False,
                "reason": "Response appears to be a question rather than an answer",
                "confidence": 0.6,
            }

        if not context:
            return {
                "on_topic": True,
                "reason": "No context provided for topic check, assuming on-topic",
                "confidence": 0.5,
            }

        answer_words = set(re.findall(r"\b\w{3,}\b", text_lower := text_stripped.lower()))
        context_words = set(re.findall(r"\b\w{3,}\b", context.lower()))

        if not context_words:
            return {
                "on_topic": True,
                "reason": "Context contains no significant words",
                "confidence": 0.5,
            }

        overlap = answer_words & context_words
        overlap_ratio = len(overlap) / len(context_words) if context_words else 0

        if overlap_ratio < config.GUARDRAIL_OFFTOPIC_THRESHOLD * 0.3:
            return {
                "on_topic": False,
                "reason": f"Low keyword overlap ({overlap_ratio:.2f}) with the question context",
                "confidence": min(1.0 - overlap_ratio, 0.9),
            }

        return {
            "on_topic": True,
            "reason": "Response appears related to the question context",
            "confidence": min(overlap_ratio, 0.95),
        }

    def validate(self, text: str, context: str = "") -> Dict[str, Any]:
        injection_result = self.check_injection(text)
        offtopic_result = self.check_offtopic(text, context)

        safe = injection_result["safe"]
        on_topic = offtopic_result["on_topic"]

        combined_confidence = min(
            injection_result["confidence"],
            offtopic_result["confidence"],
        )

        return {
            "safe": safe,
            "on_topic": on_topic,
            "valid": safe and on_topic,
            "injection": injection_result,
            "offtopic": offtopic_result,
            "confidence": combined_confidence,
        }
