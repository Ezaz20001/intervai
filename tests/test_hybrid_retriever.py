from unittest.mock import MagicMock

from backend.rag.hybrid_retriever import HybridRetriever


def test_retrieve_skills_calls_store():
    mock_store = MagicMock()
    mock_store.similarity_search.return_value = [
        {"id": "1", "text": "Python expert", "metadata": {"source": "cv"}}
    ]
    retriever = HybridRetriever(vector_store=mock_store, db=MagicMock())
    results = retriever.retrieve_skills_context("user1", "Python skills")
    mock_store.similarity_search.assert_called_once_with(
        query="Python skills",
        n_results=5,
        filter_metadata={"user_id": "user1", "source": "cv"},
    )
    assert len(results) == 1
    assert results[0]["text"] == "Python expert"


def test_retrieve_projects_calls_store():
    mock_store = MagicMock()
    mock_store.similarity_search.return_value = [
        {"id": "2", "text": "Built a project management tool", "metadata": {"topic": "projects"}}
    ]
    retriever = HybridRetriever(vector_store=mock_store, db=MagicMock())
    results = retriever.retrieve_projects_context("user1", "project experience")
    mock_store.similarity_search.assert_called_once()
    assert len(results) == 1


def test_retrieve_all_combines_results():
    mock_store = MagicMock()
    mock_store.similarity_search.side_effect = [
        [{"id": "1", "text": "skill result", "metadata": {"source": "cv"}}],
        [{"id": "2", "text": "project result", "metadata": {"topic": "project work"}}],
    ]
    retriever = HybridRetriever(vector_store=mock_store, db=MagicMock())
    results = retriever.retrieve_all_context("user1", "tell me about experience")
    assert "skills" in results
    assert "projects" in results
    assert len(results["skills"]) == 1
    assert len(results["projects"]) == 1
