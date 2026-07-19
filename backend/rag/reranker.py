from typing import List, Dict, Any, Optional

from backend import config


class CrossEncoderReranker:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.CROSS_ENCODER_MODEL
        self._model = None

    def _ensure_loaded(self):
        if self._model is not None:
            return
        from sentence_transformers import CrossEncoder
        self._model = CrossEncoder(self.model_name)

    def rerank(
        self, query: str, documents: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        if not documents:
            return []

        self._ensure_loaded()

        pairs = [(query, doc.get("text", "")) for doc in documents]
        scores = self._model.predict(pairs)

        for doc, score in zip(documents, scores):
            doc["rerank_score"] = float(score)

        reranked = sorted(documents, key=lambda d: d["rerank_score"], reverse=True)
        return reranked[:top_k]
