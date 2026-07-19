from unittest.mock import MagicMock, patch

from backend.rag.reranker import CrossEncoderReranker


def test_rerank_returns_sorted():
    reranker = CrossEncoderReranker()
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.3, 0.9, 0.6]
    reranker._model = mock_model

    docs = [
        {"id": "1", "text": "low relevance"},
        {"id": "2", "text": "high relevance"},
        {"id": "3", "text": "medium relevance"},
    ]
    result = reranker.rerank("test query", docs, top_k=3)

    assert len(result) == 3
    assert result[0]["text"] == "high relevance"
    assert result[1]["text"] == "medium relevance"
    assert result[2]["text"] == "low relevance"
    assert result[0]["rerank_score"] == 0.9


def test_rerank_respects_top_k():
    reranker = CrossEncoderReranker()
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.2, 0.8, 0.5, 0.9, 0.1]
    reranker._model = mock_model

    docs = [
        {"id": "1", "text": "doc one"},
        {"id": "2", "text": "doc two"},
        {"id": "3", "text": "doc three"},
        {"id": "4", "text": "doc four"},
        {"id": "5", "text": "doc five"},
    ]
    result = reranker.rerank("test query", docs, top_k=2)

    assert len(result) == 2
    assert result[0]["rerank_score"] >= result[1]["rerank_score"]
