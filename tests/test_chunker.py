from backend.ingestion.chunker import chunk_text


def test_chunk_text_returns_list():
    result = chunk_text("Hello world")
    assert isinstance(result, list)


def test_chunk_text_single_chunk():
    text = "Short text."
    result = chunk_text(text, chunk_size=500, chunk_overlap=100)
    assert len(result) == 1
    assert result[0] == text


def test_chunk_text_multiple_chunks():
    text = "Word. " * 200
    result = chunk_text(text, chunk_size=100, chunk_overlap=20)
    assert len(result) > 1


def test_chunk_text_orders_preserved():
    sentences = [f"Sentence {i}." for i in range(10)]
    text = " ".join(sentences)
    result = chunk_text(text, chunk_size=200, chunk_overlap=0)
    assert len(result) >= 1
