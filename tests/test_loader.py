import tempfile
from pathlib import Path

from backend.ingestion.loader import load_document


def test_load_txt():
    content = "Hello, this is a test document."
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp_path = f.name
    try:
        result = load_document(tmp_path)
        assert result == content
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_load_txt_multiline():
    lines = ["Line 1", "Line 2", "Line 3"]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("\n".join(lines))
        tmp_path = f.name
    try:
        result = load_document(tmp_path)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_load_unsupported_format():
    try:
        load_document("test.unsupported")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unsupported" in str(e)
