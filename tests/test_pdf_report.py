import os
from unittest.mock import MagicMock, patch

from backend.reports.pdf_report import ReportGenerator


def test_report_generation():
    mock_db = MagicMock()
    mock_db.get_session.return_value = {
        "id": 1,
        "user_id": "test_user",
        "job_role": "Software Engineer",
        "started_at": "2025-01-15T10:00:00",
        "ended_at": "2025-01-15T10:30:00",
    }
    mock_db.get_session_answers.return_value = [
        {
            "question": "Tell me about yourself",
            "answer": "I am a software engineer with five years experience",
            "score": 8,
            "topic": "experience",
            "feedback_text": "Good answer with clear strengths",
        }
    ]
    generator = ReportGenerator()
    output_path = os.path.join("data", "reports", "test_report.pdf")
    result = generator.generate_session_report(1, mock_db, output_path=output_path)
    assert result is not None
    assert isinstance(result, str)


def test_report_creates_file():
    mock_db = MagicMock()
    mock_db.get_session.return_value = {
        "id": 2,
        "user_id": "test_user",
        "job_role": "Data Scientist",
        "started_at": "2025-01-15T10:00:00",
        "ended_at": "2025-01-15T10:45:00",
    }
    mock_db.get_session_answers.return_value = [
        {
            "question": "Describe a challenging project",
            "answer": "I built a machine learning pipeline that processed millions of records",
            "score": 7,
            "topic": "technical",
            "feedback_text": "Strong technical response",
        }
    ]
    generator = ReportGenerator()
    output_path = os.path.join("data", "reports", "test_report_creates.pdf")
    result = generator.generate_session_report(2, mock_db, output_path=output_path)
    assert os.path.exists(result)
    os.remove(result)
