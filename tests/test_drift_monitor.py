from unittest.mock import MagicMock

from backend.evaluation.drift_monitor import DriftMonitor


def test_stable_scores_no_drift():
    mock_db = MagicMock()
    mock_db.get_user_sessions.return_value = [{"id": 1}, {"id": 2}, {"id": 3}]
    answers_map = {
        1: [{"score": 8}, {"score": 7}],
        2: [{"score": 8}, {"score": 9}],
        3: [{"score": 7}, {"score": 8}],
    }
    mock_db.get_session_answers.side_effect = lambda sid: answers_map[sid]
    monitor = DriftMonitor(db=mock_db)
    result = monitor.check_drift("user1")
    assert result["drifting"] is False
    assert isinstance(result["z_score"], float)
    assert isinstance(result["recent_avg"], float)


def test_dropping_scores_drift():
    mock_db = MagicMock()
    mock_db.get_user_sessions.return_value = [
        {"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5},
    ]
    answers_map = {
        1: [{"score": 9}, {"score": 9}],
        2: [{"score": 10}, {"score": 9}],
        3: [{"score": 9}, {"score": 10}],
        4: [{"score": 9}, {"score": 9}],
        5: [{"score": 1}, {"score": 1}],
    }
    mock_db.get_session_answers.side_effect = lambda sid: answers_map[sid]
    monitor = DriftMonitor(db=mock_db)
    result = monitor.check_drift("user1")
    assert result["drifting"] is True
    assert result["z_score"] < 0


def test_empty_history_no_drift():
    mock_db = MagicMock()
    mock_db.get_user_sessions.return_value = []
    monitor = DriftMonitor(db=mock_db)
    result = monitor.check_drift("user1")
    assert result["drifting"] is False
    assert result["z_score"] == 0.0
    assert result["recent_avg"] == 0.0
