from backend.emotion.analyzer import analyze_text


def test_analyze_text_returns_dict():
    result = analyze_text("I am very confident about this answer.")
    assert isinstance(result, dict)


def test_analyze_text_has_keys():
    result = analyze_text("This is a test answer.")
    expected_keys = {"confidence_score", "filler_count", "sentiment", "filler_words"}
    assert expected_keys.issubset(result.keys())


def test_analyze_text_confidence_in_range():
    result = analyze_text("I am extremely confident and well prepared for this interview.")
    score = result["confidence_score"]
    assert 1 <= score <= 10


def test_analyze_text_detects_fillers():
    result = analyze_text("Like, um, I think, you know, this is my answer.")
    assert result["filler_count"] > 0
    assert len(result["filler_words"]) > 0


def test_analyze_text_no_fillers():
    result = analyze_text("This answer contains no filler words at all.")
    assert result["filler_count"] == 0


def test_analyze_text_sentiment_structure():
    result = analyze_text("I love this! It is absolutely wonderful and amazing.")
    sent = result["sentiment"]
    assert "pos" in sent
    assert "neg" in sent
    assert "neu" in sent
    assert "compound" in sent
