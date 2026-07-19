import json
from unittest.mock import MagicMock

from backend.grader.star_grader import STARGrader


def test_grading_prompt_contains_star():
    grader = STARGrader()
    prompt = grader._build_grading_prompt()
    assert "STAR" in prompt
    assert "Situation" in prompt
    assert "Task" in prompt
    assert "Action" in prompt
    assert "Result" in prompt


def test_parse_valid_json():
    grader = STARGrader()
    response = json.dumps({
        "star_score": 8,
        "coherence_score": 7,
        "keyword_score": 9,
        "overall_score": 8,
        "matched_keywords": ["Python", "Docker"],
        "missing_keywords": ["Kubernetes"],
        "star_components": {
            "situation": True,
            "task": True,
            "action": True,
            "result": False,
        },
        "reasoning": "Strong answer with good structure.",
    })
    result = grader._parse_grading_response(response)
    assert result["star_score"] == 8
    assert result["coherence_score"] == 7
    assert result["keyword_score"] == 9
    assert result["overall_score"] == 8
    assert "Python" in result["matched_keywords"]
    assert "Kubernetes" in result["missing_keywords"]
    assert result["star_components"]["situation"] is True
    assert result["star_components"]["result"] is False


def test_parse_invalid_json_fallback():
    grader = STARGrader()
    raw = 'Some garbage text "star_score": 6 "coherence_score": 4 "keyword_score": 7 "overall_score": 5'
    result = grader._parse_grading_response(raw)
    assert result["star_score"] == 6
    assert result["coherence_score"] == 4
    assert result["keyword_score"] == 7
    assert result["overall_score"] == 5
    assert isinstance(result["matched_keywords"], list)
    assert isinstance(result["missing_keywords"], list)


def test_grade_returns_expected_fields():
    grader = STARGrader()
    mock_llm = MagicMock()
    mock_llm._call.return_value = json.dumps({
        "star_score": 7,
        "coherence_score": 8,
        "keyword_score": 6,
        "overall_score": 7,
        "matched_keywords": ["Python"],
        "missing_keywords": ["Go"],
        "star_components": {
            "situation": True,
            "task": True,
            "action": True,
            "result": True,
        },
        "reasoning": "Good answer.",
    })
    result = grader.grade_answer(
        question="Tell me about a project.",
        answer="I built a web app using Python and Flask.",
        job_context="Python developer needed",
        llm_service=mock_llm,
    )
    assert "star_score" in result
    assert "coherence_score" in result
    assert "keyword_score" in result
    assert "overall_score" in result
    assert "matched_keywords" in result
    assert "missing_keywords" in result
    assert "star_components" in result
    assert "reasoning" in result
    mock_llm._call.assert_called_once()
